import { Empty, Typography } from 'antd';
import type { ReactNode } from 'react';

interface EmptyStateProps {
  title: string;
  hint?: string;
  action?: ReactNode;
}

export const EmptyState = ({ title, hint, action }: EmptyStateProps) => (
  <Empty
    image={Empty.PRESENTED_IMAGE_SIMPLE}
    description={
      <span>
        <Typography.Text>{title}</Typography.Text>
        {hint && (
          <>
            <br />
            <Typography.Text type="secondary">{hint}</Typography.Text>
          </>
        )}
      </span>
    }
  >
    {action}
  </Empty>
);
