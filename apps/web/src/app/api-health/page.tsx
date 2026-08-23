import ApiHealthStatus from "../api-health-status";

export default function ApiHealthPage() {
  return (
    <main className="shell">
      <p className="eyebrow">Margin development</p>
      <h1>Checking the local API.</h1>
      <ApiHealthStatus />
    </main>
  );
}
