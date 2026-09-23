import { Tag } from 'antd';

import type { MatchedBy } from '@/shared/api/search';
import { MATCHED_BY_LABELS } from '@/shared/lib/labels';

const MATCHED_BY_COLORS: Record<MatchedBy, string> = {
  keyword: 'geekblue',
  semantic: 'purple',
};

interface MatchedByTagsProps {
  matchedBy: MatchedBy[];
}

export const MatchedByTags = ({ matchedBy }: MatchedByTagsProps) =>
  matchedBy.map(source => (
    <Tag
      key={source}
      variant="outlined"
      color={MATCHED_BY_COLORS[source]}
      style={{ marginInlineEnd: 0 }}
    >
      {MATCHED_BY_LABELS[source]}
    </Tag>
  ));
