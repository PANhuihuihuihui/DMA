import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppDemo, LandingPage } from "../main.jsx";
import { DebugRoute } from "./DebugRoute.jsx";

export function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/app" element={<AppDemo />} />
        <Route path="/app/debug" element={<DebugRoute />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
