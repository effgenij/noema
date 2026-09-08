import { createFileRoute } from "@tanstack/react-router";
import { dbHealth } from "~/server/db";

export const Route = createFileRoute("/")({
    loader: () => dbHealth(),
    component: Dashboard,
});

function Dashboard() {
    const domains = ["notes", "projects", "todo", "habits", "calendar"];
    const health = Route.useLoaderData();
    return (
        <main>
            <h1>Noema</h1>
            <p>self-hosted workspace</p>
            <ul>
                {domains.map((d) => (
                    <li key={d}>{d}</li>
                ))}
            </ul>
            <p data-testid="db-health">db: {health.ok ? "connected" : "unreachable"}</p>
        </main>
    );
}