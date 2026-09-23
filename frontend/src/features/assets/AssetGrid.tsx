import { Col, Row } from 'antd';

import { getErrorMessage } from '@/shared/api/http-client';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorState } from '@/shared/ui/ErrorState';

import { AssetCard, type AssetCardItem } from './AssetCard';
import { AssetGridSkeleton } from './AssetGridSkeleton';

interface AssetGridProps {
  assets: AssetCardItem[];
  isLoading: boolean;
  error: unknown;
  onRetry: () => void;
  /** The active search text, or null when the full list is shown. Picks the empty-state copy. */
  activeQuery: string | null;
  onOpen: (assetId: string) => void;
}

export const AssetGrid = ({ assets, isLoading, error, onRetry, activeQuery, onOpen }: AssetGridProps) => {
  if (isLoading) {
    return <AssetGridSkeleton />;
  }
  if (error) {
    return (
      <ErrorState
        message={getErrorMessage(error)}
        onRetry={onRetry}
      />
    );
  }
  if (assets.length === 0) {
    return activeQuery === null ? (
      <EmptyState
        title="Upload your first file to start"
        hint="Text files and images are welcome."
      />
    ) : (
      <EmptyState
        title={`No results for “${activeQuery}”.`}
        hint="Try other words."
      />
    );
  }

  return (
    <Row gutter={[16, 16]}>
      {assets.map(asset => (
        <Col
          key={asset.id}
          xs={24}
          sm={12}
          md={8}
          lg={6}
        >
          <AssetCard
            asset={asset}
            onOpen={onOpen}
          />
        </Col>
      ))}
    </Row>
  );
};
