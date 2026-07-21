import React from "react";
import ReactDOM from "react-dom/client";
import { HelmetProvider } from "react-helmet-async";
import { AuthProvider } from "./hooks/useAuth";
import { DeviceProvider } from "./hooks/useDevice";
import ErrorBoundary from "./components/ErrorBoundary";
import App from "./App";
import RadioPopoutWindow from "./components/RadioPopoutWindow";
import "./index.css";
import { initializeExperiments } from "./experiments";

const BUILD_TIMESTAMP = "2026-04-06T07:53:00Z";

initializeExperiments();

const isRadioPopout =
  typeof window !== "undefined" &&
  new URLSearchParams(window.location.search).get("radio_popout") === "1";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <HelmetProvider>
      <ErrorBoundary>
        {isRadioPopout ? (
          <RadioPopoutWindow />
        ) : (
          <DeviceProvider>
            <AuthProvider>
              <App />
            </AuthProvider>
          </DeviceProvider>
        )}
      </ErrorBoundary>
    </HelmetProvider>
  </React.StrictMode>
);
