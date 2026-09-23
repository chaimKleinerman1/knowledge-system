import { ExclamationCircleOutlined, SyncOutlined } from '@ant-design/icons';
import { Tag, Tooltip } from 'antd';

import type { AssetResponse } from '@/shared/api/assets';

interface AssetStatusBadgeProps {
  asset: Pick<AssetResponse, 'status' | 'error'>;
}

/** Ready files show no badge: it is the normal state. */
export const AssetStatusBadge = ({ asset }: AssetStatusBadgeProps) => {
  if (asset.status === 'processing') {
    return (
      <Tag
        icon={<SyncOutlined spin />}
        color="processing"
        style={{ marginInlineEnd: 0 }}
      >
        Processing
      </Tag>
    );
  }
  if (asset.status === 'failed') {
    return (
      <Tooltip title={asset.error ?? 'The AI analysis failed.'}>
        <Tag
          icon={<ExclamationCircleOutlined />}
          color="error"
          style={{ marginInlineEnd: 0 }}
        >
          Failed
        </Tag>
      </Tooltip>
    );
  }
  return null;
};
