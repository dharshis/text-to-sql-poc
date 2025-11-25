/**
 * DataVisualization component - Auto-detecting chart visualization.
 *
 * Automatically selects chart type based on data structure:
 * - Date columns → LineChart
 * - 2 columns with numeric → BarChart
 * - Percentage/proportion → PieChart
 * - Default → BarChart
 */

import React from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Box, Typography, Paper } from '@mui/material';

// Color palette for charts
const COLORS = ['#1976d2', '#4caf50', '#ff9800', '#f44336', '#9c27b0', '#00bcd4'];

/**
 * Detect appropriate chart type based on data structure.
 */
const detectChartType = (data, columns) => {
  if (!data || data.length === 0 || !columns || columns.length === 0) {
    return 'bar'; // Default
  }

  // Check for date columns
  const hasDateColumn = columns.some((col) =>
    /date|time|month|quarter|year/i.test(col)
  );
  if (hasDateColumn) {
    return 'line';
  }

  // Check for percentage/proportion columns
  const hasPercentage = columns.some((col) =>
    /percent|%|share|proportion|ratio/i.test(col)
  );
  if (hasPercentage && data.length <= 10) {
    return 'pie';
  }

  // Default to bar chart for comparisons
  return 'bar';
};

/**
 * Get appropriate keys for X and Y axes.
 */
const getChartKeys = (columns) => {
  if (columns.length === 0) return { xKey: null, yKeys: [] };

  // First column is typically the category/label
  const xKey = columns[0];

  // Remaining numeric columns are data values
  const yKeys = columns.slice(1).filter((col) => {
    // Filter out obviously non-numeric columns
    return !/id|name|description/i.test(col);
  });

  return { xKey, yKeys };
};

/**
 * Format large numbers for display.
 */
const formatNumber = (value) => {
  if (typeof value !== 'number') return value;
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
  return value.toFixed(2);
};

const DataVisualization = ({ data, columns }) => {
  if (!data || data.length === 0) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          No data to visualize
        </Typography>
      </Paper>
    );
  }

  const chartType = detectChartType(data, columns);
  const { xKey, yKeys } = getChartKeys(columns);

  if (!xKey || yKeys.length === 0) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          Unable to visualize this data structure
        </Typography>
      </Paper>
    );
  }

  const renderChart = () => {
    switch (chartType) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xKey} angle={-45} textAnchor="end" height={80} />
              <YAxis tickFormatter={formatNumber} />
              <Tooltip formatter={formatNumber} />
              <Legend />
              {yKeys.map((key, index) => (
                <Line
                  key={key}
                  type="monotone"
                  dataKey={key}
                  stroke={COLORS[index % COLORS.length]}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'pie':
        // For pie charts, use first numeric column
        const pieKey = yKeys[0];
        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={data}
                dataKey={pieKey}
                nameKey={xKey}
                cx="50%"
                cy="50%"
                outerRadius={120}
                label={(entry) => `${entry[xKey]}: ${formatNumber(entry[pieKey])}`}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={formatNumber} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );

      case 'bar':
      default:
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xKey} angle={-45} textAnchor="end" height={80} />
              <YAxis tickFormatter={formatNumber} />
              <Tooltip formatter={formatNumber} />
              <Legend />
              {yKeys.map((key, index) => (
                <Bar
                  key={key}
                  dataKey={key}
                  fill={COLORS[index % COLORS.length]}
                  radius={[8, 8, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Data Visualization{' '}
        <Typography component="span" variant="body2" color="text.secondary">
          ({chartType} chart, {data.length} data points)
        </Typography>
      </Typography>
      <Box sx={{ mt: 2 }}>{renderChart()}</Box>
    </Paper>
  );
};

export default DataVisualization;
