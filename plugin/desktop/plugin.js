/**
 * Cortex — desktop half. Loaded by Hermes Desktop from
 * ~/.hermes/plugins/cortex/desktop/plugin.js (uncompiled ESM).
 * Only @hermes/plugin-sdk, react, react/jsx-runtime resolve.
 *
 * Tasks kanban: 3 columns, add form, status change, delete.
 * UI updates via polling (refetchInterval 3s) — no event API (T2 research).
 */
import {
  useQuery,
  ROUTES_AREA,
  SIDEBAR_NAV_AREA,
} from "@hermes/plugin-sdk";
import { jsx, jsxs } from "react/jsx-runtime";
import { useState } from "react";

const COLUMNS = [
  { status: "todo", label: "Todo" },
  { status: "in_progress", label: "In progress" },
  { status: "done", label: "Done" },
];

function TaskCard({ task, onMove, onDelete }) {
  return jsxs(
    "div",
    {
      className:
        "flex flex-col gap-1 rounded-md border border-(--ui-stroke-secondary) bg-(--ui-bg) p-2 text-sm",
      children: [
        jsx("div", { className: "font-medium", children: task.title }),
        task.due
          ? jsx("div", {
              className: "text-xs text-(--ui-text-tertiary)",
              children: `due ${task.due}`,
            })
          : null,
        jsxs("div", {
          className: "flex items-center gap-1",
          children: [
            jsx("select", {
              className:
                "min-w-0 flex-1 rounded border border-(--ui-stroke-secondary) bg-transparent px-1 py-0.5 text-xs",
              value: task.status,
              onChange: (e) => onMove(task, e.target.value),
              children: COLUMNS.map((c) =>
                jsx("option", { value: c.status, children: c.label }, c.status),
              ),
            }),
            jsx("button", {
              type: "button",
              className:
                "rounded px-1 text-xs text-(--ui-text-tertiary) hover:bg-(--chrome-action-hover) hover:text-foreground",
              onClick: () => onDelete(task),
              children: "✕",
            }),
          ],
        }),
      ],
    },
    task.id,
  );
}

function CortexTasks({ ctx }) {
  const [title, setTitle] = useState("");
  const tasks = useQuery({
    queryKey: ["cortex", "tasks"],
    queryFn: () => ctx.rest("/tasks"),
    refetchInterval: 3000,
  });

  const refresh = () => tasks.refetch();

  const create = async () => {
    const value = title.trim();
    if (!value) return;
    setTitle("");
    await ctx.rest("/tasks", { method: "POST", body: { title: value } });
    refresh();
  };

  const move = async (task, status) => {
    await ctx.rest(`/tasks/${task.id}`, { method: "PATCH", body: { status } });
    refresh();
  };

  const remove = async (task) => {
    await ctx.rest(`/tasks/${task.id}`, { method: "DELETE" });
    refresh();
  };

  const list = tasks.data ?? [];

  return jsxs("div", {
    className: "flex h-full flex-col gap-3 p-3 text-sm",
    children: [
      jsx("div", { className: "font-medium", children: "Cortex — Tasks" }),
      jsxs("div", {
        className: "flex gap-2",
        children: [
          jsx("input", {
            className:
              "min-w-0 flex-1 rounded border border-(--ui-stroke-secondary) bg-transparent px-2 py-1",
            placeholder: "New task…",
            value: title,
            onChange: (e) => setTitle(e.target.value),
            onKeyDown: (e) => {
              if (e.key === "Enter") create();
            },
          }),
          jsx("button", {
            type: "button",
            className:
              "rounded bg-(--ui-accent) px-3 py-1 font-medium text-(--ui-base) hover:opacity-90",
            onClick: create,
            children: "Add",
          }),
        ],
      }),
      tasks.isError
        ? jsx("div", {
            className: "text-(--ui-text-tertiary)",
            children: "tasks: unreachable",
          })
        : jsxs("div", {
            className: "grid min-h-0 flex-1 grid-cols-3 gap-3",
            children: COLUMNS.map((col) =>
              jsxs(
                "div",
                {
                  className:
                    "flex min-h-0 flex-col gap-2 rounded-md bg-(--ui-bg-secondary) p-2",
                  children: [
                    jsx("div", {
                      className:
                        "text-xs font-medium uppercase tracking-wide text-(--ui-text-tertiary)",
                      children: `${col.label} (${list.filter((t) => t.status === col.status).length})`,
                    }),
                    jsxs("div", {
                      className:
                        "flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto",
                      children: list
                        .filter((t) => t.status === col.status)
                        .map((t) =>
                          jsx(
                            TaskCard,
                            { task: t, onMove: move, onDelete: remove },
                            t.id,
                          ),
                        ),
                    }),
                  ],
                },
                col.status,
              ),
            ),
          }),
    ],
  });
}

export default {
  id: "cortex", // must match the folder name
  name: "Cortex",
  register(ctx) {
    ctx.registerMany([
      {
        id: "home",
        area: ROUTES_AREA,
        data: { path: "/cortex" },
        render: () => jsx(CortexTasks, { ctx }),
      },
      {
        id: "nav",
        area: SIDEBAR_NAV_AREA,
        data: { path: "/cortex", label: "Cortex", codicon: "home" },
      },
    ]);
  },
};
