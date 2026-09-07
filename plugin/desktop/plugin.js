/**
 * Cortex — desktop half. Loaded by Hermes Desktop from
 * ~/.hermes/plugins/cortex/desktop/plugin.js (uncompiled ESM).
 * Only @hermes/plugin-sdk, react, react/jsx-runtime resolve.
 */
import { host, useQuery, useValue, ROUTES_AREA, SIDEBAR_NAV_AREA } from '@hermes/plugin-sdk'
import { jsx, jsxs } from 'react/jsx-runtime'

function CortexHome({ ctx }) {
  const gateway = useValue(host.state.gateway)
  const health = useQuery({
    queryKey: ['cortex', 'health'],
    queryFn: () => ctx.rest('/health')
  })

  let healthLine = 'health: …'
  if (health.isError) {
    healthLine = 'health: unreachable'
  } else if (health.data) {
    healthLine = `health: ${JSON.stringify(health.data)}`
  }

  return jsxs('div', {
    className: 'flex h-full flex-col gap-2 p-3 text-sm',
    children: [
      jsx('div', { className: 'font-medium', children: 'Cortex — workspace plugin' }),
      jsx('div', { className: 'text-(--ui-text-tertiary)', children: `gateway: ${gateway}` }),
      jsx('div', { className: 'text-(--ui-text-tertiary)', children: healthLine })
    ]
  })
}

export default {
  id: 'cortex', // must match the folder name
  name: 'Cortex',
  register(ctx) {
    ctx.registerMany([
      {
        id: 'home',
        area: ROUTES_AREA,
        data: { path: '/cortex' },
        render: () => jsx(CortexHome, { ctx })
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        data: { path: '/cortex', label: 'Cortex', codicon: 'home' }
      }
    ])
  }
}
