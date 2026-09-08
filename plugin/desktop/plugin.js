/**
 * Cortex — desktop half. Loaded by Hermes Desktop from
 * ~/.hermes/plugins/cortex/desktop/plugin.js (uncompiled ESM).
 * Only @hermes/plugin-sdk, react, react/jsx-runtime resolve.
 *
 * Tasks kanban: 3 columns, add form, status change, delete.
 * UI updates via polling (refetchInterval 3s) — no event API (T2 research).
 */
import { useQuery, ROUTES_AREA, SIDEBAR_NAV_AREA } from "@hermes/plugin-sdk";
import { jsx, jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";

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

function CortexNotes({ ctx }) {
  const [selectedId, setSelectedId] = useState(null);
  const [draftTitle, setDraftTitle] = useState("");
  const [draftText, setDraftText] = useState("");
  const [draftFolder, setDraftFolder] = useState("");
  const notes = useQuery({
    queryKey: ["cortex", "notes"],
    queryFn: () => ctx.rest("/notes"),
    refetchInterval: 3000,
  });
  const folders = useQuery({
    queryKey: ["cortex", "notes-folders"],
    queryFn: () => ctx.rest("/notes/folders"),
    refetchInterval: 3000,
  });

  const list = notes.data ?? [];
  const folderList = folders.data ?? [];
  const selected = list.find((n) => n.id === selectedId) ?? null;

  const bodyOf = (n) => {
    try {
      return JSON.parse(n.content).text ?? "";
    } catch {
      return n.content ?? "";
    }
  };

  // Live-sync the open editor when the selected note changes on the server
  // (agent append via polling): re-sync drafts whenever id or updated_at moves.
  useEffect(() => {
    if (selected) {
      setDraftTitle(selected.title);
      setDraftText(bodyOf(selected));
      setDraftFolder(selected.folder ?? "");
    }
  }, [selected?.id, selected?.updated_at]);

  const refresh = () => {
    notes.refetch();
    folders.refetch();
  };

  const select = (n) => {
    setSelectedId(n.id);
    setDraftTitle(n.title);
    setDraftText(bodyOf(n));
    setDraftFolder(n.folder ?? "");
  };

  const create = async () => {
    const note = await ctx.rest("/notes", {
      method: "POST",
      body: { title: "Untitled" },
    });
    refresh();
    select(note);
  };

  const save = async () => {
    if (!selected) return;
    if (!draftTitle.trim()) return;
    await ctx.rest(`/notes/${selected.id}`, {
      method: "PATCH",
      body: { title: draftTitle, text: draftText, folder: draftFolder },
    });
    refresh();
  };

  const remove = async () => {
    if (!selected) return;
    await ctx.rest(`/notes/${selected.id}`, { method: "DELETE" });
    setSelectedId(null);
    refresh();
  };

  const itemCls = (active) =>
    `rounded px-2 py-1 text-left text-sm ${
      active
        ? "bg-(--ui-control-active-background) text-foreground"
        : "text-(--ui-text-secondary) hover:bg-(--chrome-action-hover)"
    }`;

  const rootNotes = list.filter((n) => !n.folder);
  const tree = folderList.map((f) => ({
    folder: f,
    notes: list.filter((n) => n.folder === f),
  }));

  return jsxs("div", {
    className: "flex h-full gap-3 p-3 text-sm",
    children: [
      jsxs("div", {
        className:
          "flex w-56 min-w-0 flex-col gap-1 overflow-y-auto rounded-md bg-(--ui-bg-secondary) p-2",
        children: [
          jsx("div", { className: "font-medium", children: "Notes" }),
          jsx("button", {
            type: "button",
            className:
              "rounded bg-(--ui-accent) px-2 py-1 text-left text-sm font-medium text-(--ui-base) hover:opacity-90",
            onClick: create,
            children: "+ New note",
          }),
          rootNotes.map((n) =>
            jsx(
              "button",
              {
                type: "button",
                className: itemCls(n.id === selectedId),
                onClick: () => select(n),
                children: n.title,
              },
              n.id,
            ),
          ),
          tree.map((g) =>
            jsxs(
              "div",
              {
                className: "flex flex-col gap-1",
                children: [
                  jsx("div", {
                    className:
                      "px-2 pt-2 text-xs font-medium uppercase tracking-wide text-(--ui-text-tertiary)",
                    children: g.folder,
                  }),
                  g.notes.map((n) =>
                    jsx(
                      "button",
                      {
                        type: "button",
                        className: itemCls(n.id === selectedId),
                        onClick: () => select(n),
                        children: n.title,
                      },
                      n.id,
                    ),
                  ),
                ],
              },
              g.folder,
            ),
          ),
        ],
      }),
      selected
        ? jsxs("div", {
            className: "flex min-w-0 flex-1 flex-col gap-2",
            children: [
              jsx("input", {
                className:
                  "rounded border border-(--ui-stroke-secondary) bg-transparent px-2 py-1 font-medium",
                value: draftTitle,
                onChange: (e) => setDraftTitle(e.target.value),
                placeholder: "Title",
              }),
              jsx("input", {
                className:
                  "rounded border border-(--ui-stroke-secondary) bg-transparent px-2 py-1 text-xs",
                value: draftFolder,
                onChange: (e) => setDraftFolder(e.target.value),
                placeholder: "Folder",
              }),
              jsx("textarea", {
                className:
                  "min-h-0 flex-1 resize-none rounded border border-(--ui-stroke-secondary) bg-transparent px-2 py-1",
                value: draftText,
                onChange: (e) => setDraftText(e.target.value),
                placeholder: "Note body…",
              }),
              jsxs("div", {
                className: "flex gap-2",
                children: [
                  jsx("button", {
                    type: "button",
                    className:
                      "rounded bg-(--ui-accent) px-3 py-1 font-medium text-(--ui-base) hover:opacity-90",
                    onClick: save,
                    children: "Save",
                  }),
                  jsx("button", {
                    type: "button",
                    className:
                      "rounded px-3 py-1 text-(--ui-text-tertiary) hover:bg-(--chrome-action-hover) hover:text-foreground",
                    onClick: remove,
                    children: "Delete",
                  }),
                ],
              }),
            ],
          })
        : jsx("div", {
            className:
              "flex flex-1 items-center justify-center text-(--ui-text-tertiary)",
            children: "Select a note",
          }),
    ],
  });
}

function Sparkline({ data }) {
  const w = 56;
  const h = 16;
  const bw = 3;
  const gap = 1;
  return jsx("svg", {
    width: w,
    height: h,
    children: data.map((v, i) =>
      jsx(
        "rect",
        {
          x: i * (bw + gap),
          y: v ? 0 : h - 2,
          width: bw,
          height: v ? h : 2,
          fill: v ? "var(--ui-accent)" : "var(--ui-stroke-secondary)",
        },
        i,
      ),
    ),
  });
}

function CortexHabits({ ctx }) {
  const [name, setName] = useState("");
  const habits = useQuery({
    queryKey: ["cortex", "habits"],
    queryFn: () => ctx.rest("/habits"),
    refetchInterval: 3000,
  });

  const list = habits.data ?? [];
  const refresh = () => habits.refetch();
  const checkedToday = (h) => h.sparkline[h.sparkline.length - 1] === 1;

  const create = async () => {
    const value = name.trim();
    if (!value) return;
    setName("");
    await ctx.rest("/habits", { method: "POST", body: { name: value } });
    refresh();
  };

  const toggle = async (h) => {
    const action = checkedToday(h) ? "uncheck" : "checkin";
    await ctx.rest(`/habits/${h.id}/${action}`, { method: "POST", body: {} });
    refresh();
  };

  const remove = async (h) => {
    await ctx.rest(`/habits/${h.id}`, { method: "DELETE" });
    refresh();
  };

  return jsxs("div", {
    className: "flex h-full flex-col gap-3 p-3 text-sm",
    children: [
      jsx("div", { className: "font-medium", children: "Cortex — Habits" }),
      jsxs("div", {
        className: "flex gap-2",
        children: [
          jsx("input", {
            className:
              "min-w-0 flex-1 rounded border border-(--ui-stroke-secondary) bg-transparent px-2 py-1",
            placeholder: "New habit…",
            value: name,
            onChange: (e) => setName(e.target.value),
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
      habits.isError
        ? jsx("div", {
            className: "text-(--ui-text-tertiary)",
            children: "habits: unreachable",
          })
        : jsxs("div", {
            className: "flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto",
            children: list.map((h) =>
              jsxs(
                "div",
                {
                  className:
                    "flex items-center gap-3 rounded-md border border-(--ui-stroke-secondary) bg-(--ui-bg) p-2",
                  children: [
                    jsx("button", {
                      type: "button",
                      className: `flex h-6 w-6 shrink-0 items-center justify-center rounded border text-xs ${
                        checkedToday(h)
                          ? "border-transparent bg-(--ui-accent) text-(--ui-base)"
                          : "border-(--ui-stroke-secondary) hover:bg-(--chrome-action-hover)"
                      }`,
                      onClick: () => toggle(h),
                      children: checkedToday(h) ? "✓" : "",
                    }),
                    jsx("div", {
                      className: "min-w-0 flex-1 truncate",
                      children: h.name,
                    }),
                    jsx("div", {
                      className:
                        "shrink-0 text-xs tabular-nums text-(--ui-text-tertiary)",
                      children: `${h.streak}d`,
                    }),
                    jsx(Sparkline, { data: h.sparkline }),
                    jsx("button", {
                      type: "button",
                      className:
                        "shrink-0 rounded px-1 text-xs text-(--ui-text-tertiary) hover:bg-(--chrome-action-hover) hover:text-foreground",
                      onClick: () => remove(h),
                      children: "✕",
                    }),
                  ],
                },
                h.id,
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
        id: "notes",
        area: ROUTES_AREA,
        data: { path: "/cortex/notes" },
        render: () => jsx(CortexNotes, { ctx }),
      },
      {
        id: "habits",
        area: ROUTES_AREA,
        data: { path: "/cortex/habits" },
        render: () => jsx(CortexHabits, { ctx }),
      },
      {
        id: "nav",
        area: SIDEBAR_NAV_AREA,
        data: { path: "/cortex", label: "Cortex", codicon: "home" },
      },
      {
        id: "nav-notes",
        area: SIDEBAR_NAV_AREA,
        data: { path: "/cortex/notes", label: "Notes", codicon: "note" },
      },
      {
        id: "nav-habits",
        area: SIDEBAR_NAV_AREA,
        data: { path: "/cortex/habits", label: "Habits", codicon: "flame" },
      },
    ]);
  },
};
