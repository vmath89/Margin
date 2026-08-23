"use client";

import { useEffect, useState } from "react";

type HealthStatus = "checking" | "available" | "unavailable";

function isHealthyResponse(value: unknown): value is { status: "ok" } {
  return (
    typeof value === "object" &&
    value !== null &&
    "status" in value &&
    value.status === "ok"
  );
}

export default function ApiHealthStatus() {
  const [healthStatus, setHealthStatus] = useState<HealthStatus>("checking");

  useEffect(() => {
    const controller = new AbortController();

    async function checkApiHealth() {
      try {
        const response = await fetch("/api/health", { signal: controller.signal });
        const body: unknown = await response.json();

        if (response.ok && isHealthyResponse(body)) {
          setHealthStatus("available");
          return;
        }
      } catch {
        // The visible unavailable state below is the development diagnostic.
      }

      if (!controller.signal.aborted) {
        setHealthStatus("unavailable");
      }
    }

    void checkApiHealth();

    return () => controller.abort();
  }, []);

  if (healthStatus === "checking") {
    return <p className="status" role="status">Checking the local API…</p>;
  }

  if (healthStatus === "available") {
    return <p className="status" role="status">The local API is connected.</p>;
  }

  return (
    <p className="status status-error" role="alert">
      The local API is unavailable. Start FastAPI at http://127.0.0.1:8000 and refresh.
    </p>
  );
}
