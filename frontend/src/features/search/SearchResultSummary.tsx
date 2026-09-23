import { Spin, Typography } from 'antd';

interface SearchResultSummaryProps {
  query: string;
  count: number | null;
  isFetching: boolean;
}

const formatCount = (count: number): string => (count === 1 ? '1 result' : `${count} results`);

export const SearchResultSummary = ({ query, count, isFetching }: SearchResultSummaryProps) => (
  <Typography.Text type="secondary">
    {count === null ? 'Searching' : formatCount(count)} for “{query}”{' '}
    {isFetching && (
      <Spin
        size="small"
        style={{ marginInlineStart: 8 }}
      />
    )}
  </Typography.Text>
);
