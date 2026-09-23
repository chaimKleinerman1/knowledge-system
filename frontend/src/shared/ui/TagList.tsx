import { Flex, Tag, Tooltip } from 'antd';

interface TagListProps {
  tags: string[];
  /** Show at most this many tags; the rest collapse into a "+N" tag with a tooltip. */
  max?: number;
  color?: string;
}

export const TagList = ({ tags, max, color }: TagListProps) => {
  const visibleTags = max === undefined ? tags : tags.slice(0, max);
  const hiddenTags = tags.slice(visibleTags.length);

  return (
    <Flex
      wrap
      gap={4}
    >
      {visibleTags.map(tag => (
        <Tag
          key={tag}
          color={color}
          style={{ marginInlineEnd: 0 }}
        >
          {tag}
        </Tag>
      ))}
      {hiddenTags.length > 0 && (
        <Tooltip title={hiddenTags.join(', ')}>
          <Tag style={{ marginInlineEnd: 0 }}>+{hiddenTags.length}</Tag>
        </Tooltip>
      )}
    </Flex>
  );
};
