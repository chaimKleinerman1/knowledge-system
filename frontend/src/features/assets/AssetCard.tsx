import './AssetCard.css';

import { Card, Flex, Tag, Typography } from 'antd';
import type { KeyboardEvent } from 'react';

import type { AssetResponse } from '@/shared/api/assets';
import type { SearchHit } from '@/shared/api/search';
import { CARD_TAG_LIMIT } from '@/shared/lib/constants';
import { formatCategory } from '@/shared/lib/labels';
import { TagList } from '@/shared/ui/TagList';

import { AssetCardCover } from './AssetCardCover';
import { AssetStatusBadge } from './AssetStatusBadge';
import { MatchedByTags } from './MatchedByTags';

export type AssetCardItem = AssetResponse | SearchHit;

interface AssetCardProps {
  asset: AssetCardItem;
  onOpen: (assetId: string) => void;
}

const getMatchedBy = (asset: AssetCardItem) => ('matched_by' in asset ? asset.matched_by : []);

export const AssetCard = ({ asset, onOpen }: AssetCardProps) => {
  const open = () => onOpen(asset.id);

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      open();
    }
  };

  return (
    <Card
      hoverable
      className="asset-card"
      cover={<AssetCardCover asset={asset} />}
      styles={{ body: { padding: 12 } }}
      role="button"
      tabIndex={0}
      aria-label={`Open ${asset.filename}`}
      onClick={open}
      onKeyDown={handleKeyDown}
    >
      <Flex
        vertical
        gap={8}
      >
        <Typography.Text
          strong
          ellipsis={{ tooltip: asset.filename }}
        >
          {asset.filename}
        </Typography.Text>
        <Flex
          wrap
          gap={4}
          align="center"
        >
          {asset.ai && (
            <Tag
              color="blue"
              style={{ marginInlineEnd: 0 }}
            >
              {formatCategory(asset.ai.category)}
            </Tag>
          )}
          <AssetStatusBadge asset={asset} />
          <MatchedByTags matchedBy={getMatchedBy(asset)} />
        </Flex>
        {asset.ai && asset.ai.tags.length > 0 && (
          <TagList
            tags={asset.ai.tags}
            max={CARD_TAG_LIMIT}
          />
        )}
      </Flex>
    </Card>
  );
};
