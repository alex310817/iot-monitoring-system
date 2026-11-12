import { lazy } from 'react';
import { Navigate } from 'react-router-dom-v5-compat';

import { config, featureEnabled } from '@grafana/runtime';
import { DashboardRoutes } from 'app/types';

import { BASE_URL as REPORTS_BASE, NEW_REPORT_URL } from './constants';

export function getReportingRoutes() {
  const routes = [];
  if (config.reporting?.enabled) {
    if (featureEnabled('reports')) {
      routes.push(
        {
          path: REPORTS_BASE,
          component: lazy(() => import(/* webpackChunkName: "ReportsListPage" */ './ReportsListPage')),
        },
        {
          path: `${REPORTS_BASE}/settings`,
          component: lazy(() => import(/* webpackChunkName: "ReportsSettingsPage" */ './ReportsSettingsPage')),
        },
        {
          path: '/d-csv/:uid',
          pageClass: 'dashboard-solo',
          routeName: DashboardRoutes.Normal,
          component: lazy(() => import(/* webpackChunkName: "CSVExportPage" */ './CSVExportPage')),
        }
      );

      if (config.featureToggles.newPDFRendering) {
        routes.push({
          path: '/d-report/:uid/:slug?',
          component: lazy(
            () => import(/* webpackChunkName: "DashboardReportPage" */ './dashboard/DashboardReportPage')
          ),
        });
      }
    } else if (config.featureToggles.featureHighlights) {
      routes.push({
        path: REPORTS_BASE,
        component: lazy(() => import(/* webpackChunkName: "ReportsUpgradePage" */ './ReportsUpgradePage')),
      });
    }

    if (featureEnabled('reports.creation')) {
      routes.push({
        path: `${REPORTS_BASE}/new`,
        component: () => <Navigate replace to={`/${NEW_REPORT_URL}`} />,
      });

      routes.push({
        path: `${REPORTS_BASE}/:step?/:id?`,
        component: lazy(() => import(/* webpackChunkName: "ReportPage" */ './ReportForm/ReportPage')),
      });
    }
  }
  return routes;
}
