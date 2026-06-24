import tempfile
import unittest
from pathlib import Path

from backend.app import store


class Phase3WorkspaceTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "phase3.sqlite")
        store.ensure_database(self.db_path)
        self.conn = store.connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def test_phase3_workspace_seeds_predis_style_records(self):
        workspace = store.get_phase3_workspace(self.conn)

        self.assertEqual("ok", workspace["status"])
        self.assertEqual("brandkit_aurora", workspace["brandKit"]["id"])
        self.assertIn("#2563eb", workspace["brandKit"]["colors"])
        self.assertEqual("https://auroraheatcool.example", workspace["brandKit"]["website"])
        self.assertEqual("@auroraheatcool", workspace["brandKit"]["socialHandle"])
        self.assertIn("#AnnArbor", workspace["brandKit"]["hashtags"])
        self.assertIn("title", workspace["brandKit"]["typography"])
        self.assertIn("light", workspace["brandKit"]["logos"])
        self.assertGreaterEqual(len(workspace["generatedCreatives"]), 4)
        self.assertGreaterEqual(len(workspace["calendarSlots"]), 4)
        self.assertGreaterEqual(len(workspace["contentSources"]), 1)
        self.assertGreaterEqual(len(workspace["competitorIdeas"]), 3)
        self.assertGreaterEqual(len(workspace["proofEvents"]), 1)
        self.assertGreaterEqual(len(workspace["creativeTemplates"]), 3)
        self.assertGreaterEqual(len(workspace["assetLibraryItems"]), 3)
        self.assertGreaterEqual(len(workspace["approvalReviewLinks"]), 4)
        self.assertGreaterEqual(len(workspace["approvalFeedback"]), 2)
        self.assertGreaterEqual(len(workspace["reviewNotifications"]), 1)
        self.assertGreaterEqual(len(workspace["performanceSnapshots"]), 4)
        self.assertGreaterEqual(len(workspace["analyticsInsights"]), 3)
        self.assertGreaterEqual(len(workspace["creatorStyleWorkflows"]), 1)
        self.assertGreaterEqual(len(workspace["creatorStyleOptions"]["styles"]), 3)
        self.assertEqual("lower_bound_observable_actions", workspace["analyticsSummary"]["attributionMode"])
        self.assertGreater(workspace["analyticsSummary"]["totals"]["impressions"], 0)

        platforms = {creative["platform"] for creative in workspace["generatedCreatives"]}
        self.assertTrue({"facebook", "instagram", "tiktok", "google_business"}.issubset(platforms))
        for creative in workspace["generatedCreatives"]:
            self.assertIn("proofLink", creative)
            self.assertIn("reviewLink", creative)
            self.assertIn("approvalFeedback", creative)
            self.assertIn("reviewNotifications", creative)
            self.assertGreaterEqual(len(creative["mediaAssets"]), 1)
            self.assertIn("prompt", creative["mediaAssets"][0])
            self.assertIn("metadata", creative["mediaAssets"][0])
            self.assertNotIn("access_token", str(creative).lower())

    def test_creator_style_workflow_generates_video_artifacts(self):
        before = store.get_phase3_workspace(self.conn)

        ideas_payload = store.create_creator_style_video_workflow(
            self.conn,
            {
                "prompt": "promote products that looks fancy",
                "goal": "lead more sales",
                "styleId": "motivational",
                "actorId": "local-owner",
                "templateId": "hook-proof-cta",
            },
        )

        self.assertEqual("ideas_ready", ideas_payload["workflow"]["status"])
        self.assertEqual(3, len(ideas_payload["workflow"]["ideas"]))
        self.assertEqual("motivational", ideas_payload["workflow"]["styleId"])

        generated = store.create_creator_style_video(
            self.conn,
            ideas_payload["workflow"]["id"],
            {
                "selectedIdeaId": ideas_payload["workflow"]["ideas"][0]["id"],
                "styleId": "motivational",
                "actorId": "local-owner",
                "templateId": "hook-proof-cta",
            },
        )

        self.assertEqual("generated_ready", generated["workflow"]["status"])
        self.assertEqual(generated["creative"]["id"], generated["workflow"]["creativeId"])
        self.assertEqual("creator-style video", generated["creative"]["format"])
        self.assertEqual("creator_style_video_storyboard", generated["mediaAsset"]["assetType"])
        self.assertEqual("storyboard_ready", generated["package"]["status"])
        self.assertEqual(generated["creative"]["id"], generated["calendarSlot"]["creativeId"])
        self.assertTrue(generated["creative"]["reviewLink"])
        self.assertGreaterEqual(
            len(generated["workspace"]["creatorStyleWorkflows"]),
            len(before["creatorStyleWorkflows"]) + 1,
        )
        refreshed = next(
            item for item in generated["workspace"]["generatedCreatives"] if item["id"] == generated["creative"]["id"]
        )
        self.assertTrue(any(asset["assetType"] == "creator_style_video_storyboard" for asset in refreshed["mediaAssets"]))
        self.assertTrue(refreshed["ugcVoiceoverPackages"])

    def test_create_approval_feedback_persists_review_comment(self):
        workspace = store.get_phase3_workspace(self.conn)
        creative = workspace["generatedCreatives"][0]
        before = len(workspace["approvalFeedback"])

        payload = store.create_approval_feedback(
            self.conn,
            {
                "creativeId": creative["id"],
                "feedbackType": "change_request",
                "authorName": "Karen Li",
                "authorRole": "owner",
                "body": "Please make the phone CTA bigger before I approve this post.",
            },
        )

        self.assertEqual("change_request", payload["feedback"]["feedbackType"])
        self.assertEqual("open", payload["feedback"]["status"])
        self.assertEqual(creative["id"], payload["reviewLink"]["creativeId"])
        self.assertIn("/review/", payload["reviewLink"]["reviewUrl"])
        self.assertGreaterEqual(len(payload["workspace"]["approvalFeedback"]), before + 1)
        refreshed = next(item for item in payload["workspace"]["generatedCreatives"] if item["id"] == creative["id"])
        self.assertTrue(any(item["body"].startswith("Please make") for item in refreshed["approvalFeedback"]))

    def test_create_review_notification_persists_outbox_record(self):
        workspace = store.get_phase3_workspace(self.conn)
        creative = workspace["generatedCreatives"][0]
        before = len(workspace["reviewNotifications"])

        payload = store.create_review_notification(
            self.conn,
            {
                "creativeId": creative["id"],
                "recipientName": "Karen Li",
                "recipientContact": "karen@example.com",
                "channel": "email",
            },
        )

        self.assertEqual("sent_demo", payload["notification"]["status"])
        self.assertEqual("email", payload["notification"]["channel"])
        self.assertIn("/review/", payload["notification"]["body"])
        self.assertGreaterEqual(len(payload["workspace"]["reviewNotifications"]), before + 1)
        refreshed = next(item for item in payload["workspace"]["generatedCreatives"] if item["id"] == creative["id"])
        self.assertTrue(any(item["status"] == "sent_demo" for item in refreshed["reviewNotifications"]))

    def test_review_package_loads_and_accepts_feedback_by_token(self):
        workspace = store.get_phase3_workspace(self.conn)
        link = workspace["approvalReviewLinks"][0]

        package = store.get_review_package(self.conn, link["reviewToken"])

        self.assertEqual("ok", package["status"])
        self.assertEqual(link["id"], package["reviewLink"]["id"])
        self.assertIn("creative", package)
        self.assertIn("brandKit", package)
        self.assertEqual("public_review_demo", package["mode"])

        result = store.create_review_feedback(
            self.conn,
            link["reviewToken"],
            {
                "feedbackType": "approval_note",
                "authorName": "Client reviewer",
                "body": "This public review route works for the client.",
            },
        )

        self.assertEqual("ok", result["status"])
        self.assertEqual("approval_note", result["feedback"]["feedbackType"])
        self.assertTrue(any(item["body"].startswith("This public review") for item in result["review"]["feedback"]))

    def test_create_content_batch_generates_creatives_calendar_and_proof_links(self):
        before = store.get_phase3_workspace(self.conn)["usage"]
        result = store.create_content_batch(
            self.conn,
            {
                "sourcePrompt": "Emergency AC diagnostic openings this weekend",
                "objective": "drive urgent calls",
            },
        )

        self.assertEqual("generated", result["batch"]["status"])
        self.assertEqual(4, len(result["creatives"]))
        self.assertTrue(any("Emergency AC" in creative["caption"] for creative in result["creatives"]))
        self.assertTrue(all(creative["mediaAssets"] for creative in result["creatives"]))
        self.assertTrue(any(asset["assetType"] == "video_storyboard" for creative in result["creatives"] for asset in creative["mediaAssets"]))

        workspace = store.get_phase3_workspace(self.conn)
        self.assertGreater(workspace["usage"]["creditsUsed"], before["creditsUsed"])
        self.assertGreater(workspace["usage"]["mediaAssets"], before["mediaAssets"])
        self.assertGreaterEqual(len(workspace["contentBatches"]), 2)
        created_ids = {creative["id"] for creative in result["creatives"]}
        slot_ids = {slot["creativeId"] for slot in workspace["calendarSlots"]}
        self.assertTrue(created_ids.issubset(slot_ids))

    def test_create_content_source_import_persists_brief(self):
        before = store.get_phase3_workspace(self.conn)
        payload = store.create_content_source_import(
            self.conn,
            {
                "label": "Cooling service page",
                "url": "https://auroraheatcool.example/cooling",
            },
        )

        self.assertEqual("analyzed_demo", payload["source"]["status"])
        self.assertEqual("Cooling service page", payload["source"]["label"])
        self.assertIn("/cooling", payload["source"]["url"])
        self.assertIn("summary", payload["source"]["brief"])
        self.assertEqual("auroraheatcool.example", payload["source"]["extracted"]["urlHost"])
        self.assertGreaterEqual(len(payload["workspace"]["contentSources"]), len(before["contentSources"]) + 1)

    def test_create_content_source_import_accepts_image_preview(self):
        before = store.get_phase3_workspace(self.conn)
        image_data_url = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciLz4="

        payload = store.create_content_source_import(
            self.conn,
            {
                "sourceType": "image",
                "label": "Installed AC unit photo",
                "fileName": "installed-ac.svg",
                "mimeType": "image/svg+xml",
                "imageDataUrl": image_data_url,
            },
        )

        self.assertEqual("image", payload["source"]["sourceType"])
        self.assertEqual("analyzed_demo", payload["source"]["status"])
        self.assertEqual("uploaded_image", payload["source"]["extracted"]["sourceKind"])
        self.assertEqual("installed-ac.svg", payload["source"]["extracted"]["fileName"])
        self.assertEqual(image_data_url, payload["source"]["extracted"]["previewDataUrl"])
        self.assertEqual("image", payload["source"]["brief"]["inputType"])
        self.assertGreaterEqual(len(payload["workspace"]["contentSources"]), len(before["contentSources"]) + 1)

    def test_ai_assistant_reply_can_create_content_batch(self):
        workspace = store.get_phase3_workspace(self.conn)
        before_batches = len(workspace["contentBatches"])

        reply_payload = store.create_ai_assistant_reply(
            self.conn,
            {"prompt": "Give me a 3-post content calendar for AC tune-ups"},
        )

        self.assertEqual("ready", reply_payload["reply"]["status"])
        self.assertIn("calendar outline", reply_payload["reply"]["replyText"])
        self.assertEqual(3, len(reply_payload["reply"]["outline"]))
        self.assertGreaterEqual(len(reply_payload["workspace"]["aiAssistantReplies"]), 1)

        batch_payload = store.create_content_batch_from_ai_reply(self.conn, reply_payload["reply"]["id"])

        self.assertEqual("converted_to_posts", batch_payload["reply"]["status"])
        self.assertEqual("generated", batch_payload["batch"]["status"])
        self.assertEqual(4, len(batch_payload["creatives"]))
        self.assertGreaterEqual(len(batch_payload["workspace"]["contentBatches"]), before_batches + 1)

    def test_update_generated_creative_persists_editor_changes(self):
        workspace = store.get_phase3_workspace(self.conn)
        creative = workspace["generatedCreatives"][0]
        payload = store.update_generated_creative(
            self.conn,
            creative["id"],
            {
                "title": "Edited title from post studio",
                "caption": "Edited caption from the Predis-style creative editor.",
                "hashtags": ["#edited", "#local"],
                "cta": "Call after edit",
                "proofHook": "edited proof hook",
                "scheduleSlot": "Saturday 8:30 AM",
                "status": "needs_review",
            },
        )

        self.assertEqual("Edited title from post studio", payload["creative"]["title"])
        self.assertEqual(["#edited", "#local"], payload["creative"]["hashtags"])
        self.assertEqual("Saturday 8:30 AM", payload["creative"]["scheduleSlot"])
        slot = next(item for item in payload["workspace"]["calendarSlots"] if item["creativeId"] == creative["id"])
        self.assertEqual("Saturday 8:30 AM", slot["slotLabel"])

    def test_create_and_apply_creative_idea_variant_updates_creative(self):
        workspace = store.get_phase3_workspace(self.conn)
        creative = workspace["generatedCreatives"][0]

        generated = store.create_creative_idea_variants(
            self.conn,
            creative["id"],
            {"objective": "book more local AC calls"},
        )

        self.assertEqual(3, len(generated["variants"]))
        self.assertGreaterEqual(generated["variants"][0]["score"], generated["variants"][1]["score"])
        self.assertIn("rationale", generated["variants"][0]["scoreBreakdown"])
        refreshed = next(item for item in generated["workspace"]["generatedCreatives"] if item["id"] == creative["id"])
        self.assertGreaterEqual(len(refreshed["ideaVariants"]), 3)

        applied = store.apply_creative_idea_variant(self.conn, generated["variants"][0]["id"])

        self.assertEqual("applied", applied["variant"]["status"])
        self.assertEqual("variant_applied", applied["creative"]["status"])
        self.assertEqual(generated["variants"][0]["hook"], applied["creative"]["title"])
        self.assertEqual(generated["variants"][0]["caption"], applied["creative"]["caption"])
        self.assertTrue(any(item["status"] == "applied" for item in applied["creative"]["ideaVariants"]))

    def test_create_creative_bulk_variations_persists_visual_test_cards(self):
        workspace = store.get_phase3_workspace(self.conn)
        creative = workspace["generatedCreatives"][0]

        payload = store.create_creative_bulk_variations(
            self.conn,
            creative["id"],
            {"objective": "test hooks, copy, and visuals", "count": 5},
        )

        self.assertEqual(5, len(payload["variants"]))
        self.assertTrue(all(variant["status"] == "ready_to_test" for variant in payload["variants"]))
        self.assertTrue(all(variant["visualDirection"] for variant in payload["variants"]))
        self.assertTrue(any("video" in variant["format"].lower() for variant in payload["variants"]))
        refreshed = next(item for item in payload["workspace"]["generatedCreatives"] if item["id"] == creative["id"])
        self.assertGreaterEqual(len(refreshed["bulkVariants"]), 5)

    def test_create_creative_ugc_voiceover_package_persists_storyboard(self):
        workspace = store.get_phase3_workspace(self.conn)
        creative = workspace["generatedCreatives"][0]

        payload = store.create_creative_ugc_voiceover_package(
            self.conn,
            creative["id"],
            {"packageLabel": "Owner explainer UGC package"},
        )

        self.assertEqual("storyboard_ready", payload["package"]["status"])
        self.assertEqual("9:16 UGC short video", payload["package"]["exportSpec"]["format"])
        self.assertGreaterEqual(len(payload["package"]["scenes"]), 4)
        self.assertIn("voiceover", str(payload["package"]).lower())
        refreshed = next(item for item in payload["workspace"]["generatedCreatives"] if item["id"] == creative["id"])
        self.assertGreaterEqual(len(refreshed["ugcVoiceoverPackages"]), 1)

    def test_create_creative_language_variants_persists_localized_copy(self):
        workspace = store.get_phase3_workspace(self.conn)
        creative = workspace["generatedCreatives"][0]

        payload = store.create_creative_language_variants(
            self.conn,
            creative["id"],
            {"targetLanguages": ["English", "Spanish", "Chinese"]},
        )

        self.assertEqual(3, len(payload["variants"]))
        labels = {variant["languageLabel"] for variant in payload["variants"]}
        self.assertEqual({"English", "Spanish", "Chinese"}, labels)
        chinese = next(variant for variant in payload["variants"] if variant["languageLabel"] == "Chinese")
        self.assertEqual("localized", chinese["status"])
        self.assertIn("Aurora", chinese["localizedCta"])
        self.assertGreaterEqual(len(chinese["localizedHashtags"]), 1)
        refreshed = next(item for item in payload["workspace"]["generatedCreatives"] if item["id"] == creative["id"])
        self.assertGreaterEqual(len(refreshed["languageVariants"]), 3)

    def test_update_creative_media_asset_persists_layer_edit(self):
        workspace = store.get_phase3_workspace(self.conn)
        asset = workspace["generatedCreatives"][0]["mediaAssets"][0]

        payload = store.update_creative_media_asset(
            self.conn,
            asset["id"],
            {
                "layerEdit": "Move CTA above the service-area footer.",
                "status": "edited_preview",
            },
        )

        self.assertEqual("edited_preview", payload["asset"]["status"])
        self.assertEqual("Move CTA above the service-area footer.", payload["asset"]["metadata"]["lastLayerEdit"])
        self.assertGreaterEqual(len(payload["asset"]["metadata"]["layerEdits"]), 1)

    def test_update_creative_media_asset_persists_structured_layer_control(self):
        workspace = store.get_phase3_workspace(self.conn)
        asset = workspace["generatedCreatives"][0]["mediaAssets"][0]

        payload = store.update_creative_media_asset(
            self.conn,
            asset["id"],
            {
                "layerControl": {
                    "id": "headline",
                    "label": "Headline",
                    "value": "Same-week AC tune-ups this weekend",
                    "placement": "top safe zone",
                    "style": "bold_hook",
                },
                "status": "edited_preview",
            },
        )

        controls = payload["asset"]["metadata"]["layerControls"]
        headline = next(control for control in controls if control["id"] == "headline")
        self.assertEqual("Same-week AC tune-ups this weekend", headline["value"])
        self.assertEqual("top safe zone", headline["placement"])
        self.assertEqual("edited_preview", payload["asset"]["status"])
        self.assertIn("structuredLayerEdits", payload["asset"]["metadata"])

    def test_update_creative_media_layer_layout_persists_order_and_position(self):
        workspace = store.get_phase3_workspace(self.conn)
        asset = workspace["generatedCreatives"][0]["mediaAssets"][0]
        control = asset["metadata"]["layerControls"][0]

        payload = store.update_creative_media_layer_layout(
            self.conn,
            asset["id"],
            {
                "layerId": control["id"],
                "action": "move-down",
                "placement": "bottom-center",
            },
        )

        moved = next(item for item in payload["asset"]["metadata"]["layerControls"] if item["id"] == control["id"])
        self.assertEqual("layout_adjusted", payload["asset"]["status"])
        self.assertEqual("bottom-center", moved["placement"])
        self.assertEqual("layout_adjusted", moved["status"])
        self.assertGreaterEqual(moved["layout"]["order"], 1)
        self.assertIn("layerLayoutEdits", payload["asset"]["metadata"])

    def test_create_template_import_applies_template_and_asset_library_item(self):
        workspace = store.get_phase3_workspace(self.conn)
        creative = workspace["generatedCreatives"][0]
        template = workspace["creativeTemplates"][0]
        asset_item = workspace["assetLibraryItems"][0]

        payload = store.create_template_import(
            self.conn,
            {
                "creativeId": creative["id"],
                "templateId": template["id"],
                "assetLibraryItemId": asset_item["id"],
            },
        )

        rendered = str(payload)
        self.assertEqual("applied_demo", payload["importedTemplate"]["status"])
        self.assertEqual(template["id"], payload["importedTemplate"]["templateId"])
        self.assertEqual(asset_item["id"], payload["assetLibraryItem"]["id"])
        self.assertEqual("template_applied", payload["mediaAsset"]["status"])
        self.assertEqual(template["format"], payload["mediaAsset"]["format"])
        self.assertEqual(template["id"], payload["mediaAsset"]["metadata"]["templateImport"]["templateId"])
        self.assertEqual(asset_item["id"], payload["mediaAsset"]["metadata"]["premiumAsset"]["id"])
        self.assertGreaterEqual(len(payload["mediaAsset"]["metadata"]["layerControls"]), 1)
        self.assertGreaterEqual(len(payload["workspace"]["importedTemplates"]), len(workspace["importedTemplates"]) + 1)
        self.assertNotIn("access_token", rendered.lower())
        self.assertNotIn("secret", rendered.lower())

    def test_create_creative_media_variant_persists_resize_record(self):
        workspace = store.get_phase3_workspace(self.conn)
        creative = workspace["generatedCreatives"][0]
        asset = creative["mediaAssets"][0]

        payload = store.create_creative_media_variant(
            self.conn,
            asset["id"],
            {
                "aspectRatio": "9:16",
                "label": "Story/Reel resize",
            },
        )

        self.assertEqual("9:16", payload["asset"]["aspectRatio"])
        self.assertEqual("Story/Reel resize", payload["asset"]["format"])
        self.assertTrue(payload["asset"]["metadata"]["resizeVariant"])
        refreshed = next(item for item in payload["workspace"]["generatedCreatives"] if item["id"] == creative["id"])
        self.assertGreater(len(refreshed["mediaAssets"]), len(creative["mediaAssets"]))

    def test_render_creative_media_asset_persists_preview_output(self):
        workspace = store.get_phase3_workspace(self.conn)
        creative = workspace["generatedCreatives"][0]
        asset = creative["mediaAssets"][0]
        store.update_creative_media_asset(
            self.conn,
            asset["id"],
            {
                "layerControl": {
                    "id": "cta",
                    "label": "CTA",
                    "value": "Call Aurora today",
                    "placement": "bottom safe zone",
                    "style": "primary_button",
                },
            },
        )

        payload = store.render_creative_media_asset(
            self.conn,
            asset["id"],
            {
                "outputKind": "preview_svg",
                "format": "Customer-ready preview",
            },
        )

        rendered = str(payload)
        self.assertEqual("rendered_preview", payload["output"]["status"])
        self.assertEqual("image/svg+xml", payload["output"]["mimeType"])
        self.assertTrue(payload["output"]["previewDataUrl"].startswith("data:image/svg+xml"))
        self.assertIn("localpilot-rendered", payload["output"]["storageRef"])
        self.assertTrue(any(control["id"] == "cta" for control in payload["output"]["metadata"]["appliedLayerControls"]))
        refreshed = next(item for item in payload["workspace"]["generatedCreatives"] if item["id"] == creative["id"])
        refreshed_asset = next(item for item in refreshed["mediaAssets"] if item["id"] == asset["id"])
        self.assertEqual("rendered_preview", refreshed_asset["status"])
        self.assertGreaterEqual(len(refreshed_asset["renderedOutputs"]), 1)
        self.assertNotIn("access_token", rendered.lower())
        self.assertNotIn("secret", rendered.lower())

    def test_update_calendar_slot_reschedules_creative(self):
        workspace = store.get_phase3_workspace(self.conn)
        slot = workspace["calendarSlots"][0]
        payload = store.update_calendar_slot(
            self.conn,
            slot["id"],
            {
                "slotLabel": "Sunday 5:15 PM",
                "scheduledFor": "2026-06-21T17:15:00-04:00",
                "status": "scheduled",
            },
        )

        self.assertEqual("Sunday 5:15 PM", payload["slot"]["slotLabel"])
        self.assertEqual("scheduled", payload["creative"]["status"])
        self.assertEqual("Sunday 5:15 PM", payload["creative"]["scheduleSlot"])

    def test_record_proof_event_persists_lower_bound_evidence(self):
        workspace = store.get_phase3_workspace(self.conn)
        creative = workspace["generatedCreatives"][0]
        payload = store.record_proof_event(
            self.conn,
            {
                "creativeId": creative["id"],
                "eventType": "owner_confirmed_mention",
                "label": "Owner heard customer mention the post",
                "value": 3,
                "source": "manual_demo",
            },
        )

        self.assertEqual("owner_confirmed_mention", payload["event"]["eventType"])
        self.assertEqual(3, payload["event"]["value"])
        self.assertEqual(creative["id"], payload["event"]["creativeId"])
        self.assertGreaterEqual(len(payload["workspace"]["proofEvents"]), len(workspace["proofEvents"]) + 1)

    def test_create_competitor_source_analysis_generates_saved_source_and_ideas(self):
        before = store.get_phase3_workspace(self.conn)
        payload = store.create_competitor_source_analysis(
            self.conn,
            {
                "label": "Main Street HVAC competitor",
                "url": "https://facebook.com/main-street-hvac",
            },
        )

        self.assertEqual("Main Street HVAC competitor", payload["source"]["label"])
        self.assertEqual("analyzed_demo", payload["source"]["status"])
        self.assertEqual(3, len(payload["ideas"]))
        self.assertTrue(any("Timing" in idea["theme"] for idea in payload["ideas"]))
        self.assertGreater(
            len(payload["workspace"]["competitorSources"]),
            len(before["competitorSources"]),
        )
        self.assertGreater(
            len(payload["workspace"]["competitorIdeas"]),
            len(before["competitorIdeas"]),
        )
        self.assertGreater(
            payload["workspace"]["usage"]["competitorRunsUsed"],
            before["usage"]["competitorRunsUsed"],
        )

    def test_update_brand_kit_persists_voice_without_secret_fields(self):
        payload = store.update_brand_kit(
            self.conn,
            {
                "voice": {
                    "tone": "neighborly expert",
                    "audience": "local homeowners",
                    "language": "plain English",
                },
                "approvedTerms": ["same-week", "neighborly expert"],
                "website": "https://neighborly.example",
                "socialHandle": "@neighborly",
                "hashtags": ["#neighborly", "#local"],
                "typography": {"title": "Editorial service headline"},
                "logos": {"light": "brand/light.svg", "dark": "brand/dark.svg"},
                "integrations": [{"name": "Website URL", "status": "available_demo"}],
            },
        )

        rendered = str(payload)
        self.assertEqual("neighborly expert", payload["brandKit"]["voice"]["tone"])
        self.assertIn("neighborly expert", payload["brandKit"]["approvedTerms"])
        self.assertEqual("https://neighborly.example", payload["brandKit"]["website"])
        self.assertEqual("@neighborly", payload["brandKit"]["socialHandle"])
        self.assertIn("#neighborly", payload["brandKit"]["hashtags"])
        self.assertEqual("Editorial service headline", payload["brandKit"]["typography"]["title"])
        self.assertEqual("brand/dark.svg", payload["brandKit"]["logos"]["dark"])
        self.assertEqual("Website URL", payload["brandKit"]["integrations"][0]["name"])
        self.assertNotIn("secret", rendered.lower())
        self.assertNotIn("token", rendered.lower())


if __name__ == "__main__":
    unittest.main()
