import { FileTextOutlined } from '@ant-design/icons';
import { theme, Typography } from 'antd';

import type { AssetResponse } from '@/shared/api/assets';
import { DESCRIPTION_PREVIEW_CHARS } from '@/shared/lib/constants';
import { truncateText } from '@/shared/lib/truncate-text';

const COVER_HEIGHT = 160;

interface AssetCardCoverProps {
  asset: AssetResponse;
}

const describeTextAsset = (asset: AssetResponse): string => {
  if (asset.ai) {
    return truncateText(asset.ai.description, DESCRIPTION_PREVIEW_CHARS);
  }
  if (asset.status === 'failed') {
    return 'The AI analysis failed.';
  }
  return 'Waiting for the AI analysis…';
};

export const AssetCardCover = ({ asset }: AssetCardCoverProps) => {
  const { token } = theme.useToken();

  if (asset.kind === 'image') {
    return (
      <img
        src={asset.file_url}
        alt={asset.ai?.description ?? asset.filename}
        loading="lazy"
        className="asset-card__image"
        style={{ height: COVER_HEIGHT, backgroundColor: token.colorFillTertiary }}
      />
    );
  }

  return (
    <div
      className="asset-card__text-cover"
      style={{ height: COVER_HEIGHT, backgroundColor: token.colorFillTertiary }}
    >
      <FileTextOutlined style={{ fontSize: 28, color: token.colorTextSecondary }} />
      <Typography.Paragraph
        type="secondary"
        className="asset-card__description"
        style={{ marginBottom: 0 }}
      >
        {describeTextAsset(asset)}
      </Typography.Paragraph>
    </div>
  );
};
