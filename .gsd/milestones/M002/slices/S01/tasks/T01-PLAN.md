---
estimated_steps: 9
estimated_files: 1
skills_used: []
---

# T01: Wired connectSession URL param to inline Facebook Page picker — real OAuth redirects now trigger page listing and selection

Why: Backend split OAuth (D11) is complete — complete_callback redirects to the UI with connectSession param, and list_pages_for_session + select_page routes exist. But the frontend location-change useEffect only handles facebookConnected=1, ignoring connectSession. Merchants cannot complete Page selection after OAuth.

Do:
1. In main.jsx, find the URL-params useEffect (search for `params.get('facebookConnected')`). Add a branch: if connectSession param is present, call loadFacebookPages(connectSession) from publishingClient.js.
2. Store the result in new state: connectSessionPages (array of pages) and pendingConnectSession (the session token string).
3. In the Connected Accounts section, when pendingConnectSession is set, render the page picker from connectSessionPages — remove the `hidden` attribute from the `.facebook-page-picker` section or conditionally show it based on pendingConnectSession being non-empty.
4. On page card click, call selectFacebookPage(pendingConnectSession, pageId), then: call reloadFacebookConnection(), clear pendingConnectSession to empty string, and remove the connectSession search param from the URL (use navigate or window.history.replaceState to avoid a reload).
5. On error, show a toast with the error message and clear pendingConnectSession.
6. The existing 'Save page selection' button (saveSelectedFacebookPage) is demo-only; the new selectFacebookPage call is the real flow.

Done when: After OAuth redirect with connectSession param, the page picker renders with real pages from the session; clicking a page calls selectFacebookPage; the connected pages list updates; the URL param is cleared.

## Inputs

- `src/main.jsx`
- `src/api/publishingClient.js`

## Expected Output

- `src/main.jsx`

## Verification

grep -q "connectSession" src/main.jsx
