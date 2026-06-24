# LocalPilot Creator Workflow Reference

Use this reference after extracting a Scribe/Predis creator-style workflow.

## Reference Signals To Look For

- Left navigation dashboard with `Create New`, `Ad Inspirations`, `Content Library`, `Content Calendar`, `Brand & Social Accounts`, `Analytics`, and `Need help`.
- `Create Your Next Post` card grid with Image, UGC, Short Ad Video, Carousel, Faceless Video, and Product Photo Shoot.
- UGC opens a focused wizard rather than an inline pile of controls.
- Wizard uses progress dots, one primary decision per screen, Back/Continue footer, and disabled/blocked continuation until required selections exist.
- Prompt step includes a textarea plus `Generate ideas for me`.
- Style step includes Storytelling, Promotional, Motivational, and Exploratory plus aspect ratio.
- Actor step uses filters plus an avatar grid.
- Later visual/template/subtitle step uses selectable preview cards.
- Review step is sparse: post type, credit estimate, aspect ratio, then Generate.
- Generated output is a preview modal with media on the left, caption/input prompt on the right, and Publish/Edit/Download or Publish/Schedule actions.
- Schedule flow opens a modal/drawer with calendar and time controls.

## LocalPilot Implementation Targets

- Keep LocalPilot brand and local-business positioning.
- Keep backend-owned artifacts:
  - generated creative
  - media asset/storyboard
  - UGC package
  - calendar slot
- Keep publish handoff guarded by owner approval and account connection status.
- Prefer a modal wizard when the user asks for popup behavior.
- Keep every visible button wired:
  - Generate ideas calls backend workflow creation.
  - Idea/style/actor/template buttons update state.
  - Continue validates the active step.
  - Generate calls backend generation.
  - Publish opens publish modal.
  - Schedule Post opens calendar/schedule handoff.

## Do Not Copy

- Predis logo, names, watermarks, proprietary actor photos, generated media, or exact copy that is not required for structure.
- Claims that LocalPilot rendered a real video unless a real renderer is integrated.
- Scraping/cookie-based publish behavior.

## Verification Pattern

Add or update a browser smoke to click:

1. `Create New`
2. `UGC`
3. `Generate ideas for me`
4. first generated idea
5. `Continue`
6. `Motivational`
7. `Continue`
8. first actor
9. `Continue`
10. first template
11. `Continue`
12. `Generate`
13. assert generated creative, media asset, UGC package, calendar slot, Publish, and Schedule Post are visible

Capture screenshots into the task folder for:

- reference contact sheet
- LocalPilot create-new grid
- prompt step
- idea step
- style step
- actor step
- template step
- review step
- generated output step
