/// <reference types="vite/client" />
import {
  HeadContent,
  Link,
  Scripts,
  createRootRoute,
} from "@tanstack/react-router";
import * as React from "react";

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "Noema" },
      {
        name: "description",
        content:
          "self-hosted OSS workspace: notes / projects / todo / habits / calendar",
      },
    ],
  }),
  shellComponent: RootDocument,
});

function RootDocument({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        <nav>
          <Link to="/" activeOptions={{ exact: true }}>
            Dashboard
          </Link>
        </nav>
        {children}
        <Scripts />
      </body>
    </html>
  );
}
