import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { DebugRoute } from "./DebugRoute.jsx";
import { ReviewRoute } from "./ReviewRoute.jsx";

export function AppRoutes({ appElement, landingElement }) {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={landingElement} />
        <Route path="/app" element={appElement} />
        <Route path="/app/debug" element={<DebugRoute />} />
        <Route path="/review/:token" element={<ReviewRoute />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
