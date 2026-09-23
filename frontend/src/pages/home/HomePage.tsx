import './HomePage.css';

import { Typography } from 'antd';
import { useState } from 'react';

import { AssetDetailDrawer } from '@/features/assets/AssetDetailDrawer';
import { AssetGrid } from '@/features/assets/AssetGrid';
import { useAssets } from '@/features/assets/hooks/use-assets';
import { UploadCard } from '@/features/assets/UploadCard';
import { SearchBar } from '@/features/search/SearchBar';
import { SearchResultSummary } from '@/features/search/SearchResultSummary';
import { useSearch } from '@/features/search/use-search';
import type { AssetListResponse } from '@/shared/api/assets';

const describeFileCount = ({ items, total }: AssetListResponse): string | null => {
  if (total === 0) {
    return null;
  }
  if (items.length < total) {
    return `Showing the newest ${items.length} of ${total} files. Use search to find the others.`;
  }
  return total === 1 ? '1 file' : `${total} files`;
};

export const HomePage = () => {
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const search = useSearch();
  const assets = useAssets();

  const gridAssets = search.isActive ? search.hits : (assets.data?.items ?? []);
  const gridIsLoading = search.isActive ? search.isLoading : assets.isLoading;
  const gridError = search.isActive ? search.error : assets.error;
  const retryGrid = () => {
    void (search.isActive ? search.refetch() : assets.refetch());
  };
  const fileCountText = !search.isActive && assets.data ? describeFileCount(assets.data) : null;

  return (
    <main className="home-page">
      <header className="home-page__header">
        <Typography.Title
          level={2}
          style={{ margin: 0 }}
        >
          Knowledge Base
        </Typography.Title>
        <Typography.Text type="secondary">Upload text files and images. Search by words or by meaning.</Typography.Text>
      </header>

      <section
        className="home-page__section"
        aria-label="Search"
      >
        <SearchBar />
        {search.isActive && (
          <SearchResultSummary
            query={search.query}
            // While a new query loads the cached hits belong to the previous query, so no count is shown.
            count={search.hasResult && !search.isFetching ? search.hits.length : null}
            isFetching={search.isFetching}
          />
        )}
      </section>

      <UploadCard />

      <section
        className="home-page__section"
        aria-label="Files"
      >
        {fileCountText && <Typography.Text type="secondary">{fileCountText}</Typography.Text>}
        <AssetGrid
          assets={gridAssets}
          isLoading={gridIsLoading}
          error={gridError}
          onRetry={retryGrid}
          activeQuery={search.isActive ? search.query : null}
          onOpen={setSelectedAssetId}
        />
      </section>

      <AssetDetailDrawer
        assetId={selectedAssetId}
        onClose={() => setSelectedAssetId(null)}
      />
    </main>
  );
};
