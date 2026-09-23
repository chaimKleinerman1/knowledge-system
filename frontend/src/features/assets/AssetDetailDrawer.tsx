import './AssetDetailDrawer.css';

import { DeleteOutlined, ExportOutlined, ReloadOutlined } from '@ant-design/icons';
import {
  Alert,
  App,
  Button,
  Collapse,
  Descriptions,
  Drawer,
  Flex,
  Image,
  Popconfirm,
  Skeleton,
  theme,
  Typography,
} from 'antd';

import type { AiMetadataResponse, AssetKind, AssetResponse } from '@/shared/api/assets';
import { getErrorMessage } from '@/shared/api/http-client';
import { formatBytes } from '@/shared/lib/format-bytes';
import { formatDateTime } from '@/shared/lib/format-date';
import { formatCategory, formatLanguage } from '@/shared/lib/labels';
import { ErrorState } from '@/shared/ui/ErrorState';
import { TagList } from '@/shared/ui/TagList';

import { useAsset } from './hooks/use-asset';
import { useDeleteAsset } from './hooks/use-delete-asset';
import { useReprocessAsset } from './hooks/use-reprocess-asset';

const DRAWER_WIDTH = 600;

interface AssetPreviewProps {
  asset: AssetResponse;
}

const AssetPreview = ({ asset }: AssetPreviewProps) => {
  const { token } = theme.useToken();

  if (asset.kind === 'image') {
    return (
      <Image
        src={asset.file_url}
        alt={asset.ai?.description ?? asset.filename}
        className="asset-preview-image"
      />
    );
  }
  if (asset.extracted_text) {
    return (
      <pre
        className="asset-text-block"
        style={{ backgroundColor: token.colorFillQuaternary }}
      >
        {asset.extracted_text}
      </pre>
    );
  }
  return null;
};

interface AiMetadataSectionProps {
  metadata: AiMetadataResponse;
  kind: AssetKind;
}

const AiMetadataSection = ({ metadata, kind }: AiMetadataSectionProps) => {
  const { token } = theme.useToken();
  const showImageText = kind === 'image' && Boolean(metadata.text_content);

  return (
    <Flex
      vertical
      gap={12}
    >
      <Typography.Paragraph style={{ marginBottom: 0 }}>{metadata.description}</Typography.Paragraph>
      <Descriptions
        size="small"
        column={1}
        items={[
          { key: 'category', label: 'Category', children: formatCategory(metadata.category) },
          { key: 'language', label: 'Language', children: formatLanguage(metadata.lang_code) },
          {
            key: 'tags',
            label: 'Tags',
            children: metadata.tags.length > 0 ? <TagList tags={metadata.tags} /> : 'None',
          },
          {
            key: 'keywords',
            label: 'Keywords',
            children: metadata.keywords.length > 0 ? <TagList tags={metadata.keywords} /> : 'None',
          },
          { key: 'model', label: 'Model', children: `${metadata.model} · prompt ${metadata.prompt_version}` },
          { key: 'processed', label: 'Analyzed', children: formatDateTime(metadata.processed_at) },
        ]}
      />
      {showImageText && (
        <Collapse
          size="small"
          items={[
            {
              key: 'text',
              label: metadata.text_truncated ? 'Text found in the image (cut off)' : 'Text found in the image',
              children: (
                <pre
                  className="asset-text-block"
                  style={{ backgroundColor: token.colorFillQuaternary }}
                >
                  {metadata.text_content}
                </pre>
              ),
            },
          ]}
        />
      )}
    </Flex>
  );
};

interface AssetDetailsProps {
  asset: AssetResponse;
}

const AssetDetails = ({ asset }: AssetDetailsProps) => (
  <Flex
    vertical
    gap={20}
  >
    <AssetPreview asset={asset} />
    {asset.status === 'failed' && (
      <Alert
        type="error"
        showIcon
        title="The AI analysis failed"
        description={asset.error ?? 'No details were given.'}
      />
    )}
    {asset.status === 'processing' && (
      <Alert
        type="info"
        showIcon
        title="Analyzing with AI…"
      />
    )}
    {asset.ai && (
      <AiMetadataSection
        metadata={asset.ai}
        kind={asset.kind}
      />
    )}
    <Descriptions
      title="File"
      size="small"
      column={1}
      items={[
        { key: 'type', label: 'Type', children: asset.mime_type },
        { key: 'size', label: 'Size', children: formatBytes(asset.size_bytes) },
        { key: 'created', label: 'Uploaded', children: formatDateTime(asset.created_at) },
        { key: 'updated', label: 'Updated', children: formatDateTime(asset.updated_at) },
      ]}
    />
  </Flex>
);

interface AssetDetailDrawerProps {
  assetId: string | null;
  onClose: () => void;
}

export const AssetDetailDrawer = ({ assetId, onClose }: AssetDetailDrawerProps) => {
  const { message } = App.useApp();
  const { data: asset, isLoading, error, refetch } = useAsset(assetId);
  const reprocessAsset = useReprocessAsset();
  const deleteAsset = useDeleteAsset();

  const handleRetry = () => {
    if (!asset) {
      return;
    }
    reprocessAsset.mutate(asset.id, {
      onSuccess: updated => {
        void (updated.status === 'ready'
          ? message.success('Analysis finished.')
          : message.warning(updated.error ?? 'The analysis failed again.'));
      },
      onError: mutationError => {
        void message.error(getErrorMessage(mutationError));
      },
    });
  };

  const handleDelete = () => {
    if (!asset) {
      return;
    }
    deleteAsset.mutate(asset.id, {
      onSuccess: () => {
        void message.success('File deleted.');
        onClose();
      },
      onError: mutationError => {
        void message.error(getErrorMessage(mutationError));
      },
    });
  };

  const footer = asset && (
    <Flex
      gap={8}
      wrap
      justify="flex-end"
    >
      <Button
        href={asset.file_url}
        target="_blank"
        rel="noreferrer"
        icon={<ExportOutlined />}
      >
        Open file
      </Button>
      {asset.status === 'failed' && (
        <Button
          type="primary"
          icon={<ReloadOutlined />}
          loading={reprocessAsset.isPending}
          onClick={handleRetry}
        >
          Retry analysis
        </Button>
      )}
      <Popconfirm
        title="Delete this file?"
        description="This removes the file and its AI metadata."
        okText="Delete"
        okButtonProps={{ danger: true }}
        cancelText="Cancel"
        onConfirm={handleDelete}
      >
        <Button
          danger
          icon={<DeleteOutlined />}
          loading={deleteAsset.isPending}
        >
          Delete
        </Button>
      </Popconfirm>
    </Flex>
  );

  return (
    <Drawer
      open={assetId !== null}
      onClose={onClose}
      size={DRAWER_WIDTH}
      title={asset?.filename ?? 'File details'}
      destroyOnHidden
      footer={footer}
    >
      {isLoading && (
        <Skeleton
          active
          paragraph={{ rows: 8 }}
        />
      )}
      {error && (
        <ErrorState
          message={getErrorMessage(error)}
          onRetry={() => {
            void refetch();
          }}
        />
      )}
      {asset && <AssetDetails asset={asset} />}
    </Drawer>
  );
};
