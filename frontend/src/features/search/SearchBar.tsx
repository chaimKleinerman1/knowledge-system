import { Input } from 'antd';
import { useAtom } from 'jotai';
import { type ChangeEvent, useState } from 'react';

import { SEARCH_DEBOUNCE_MS, SEARCH_PLACEHOLDER } from '@/shared/lib/constants';
import { useDebouncedCallback } from '@/shared/lib/use-debounced-callback';

import { searchQueryAtom } from './atoms';

export const SearchBar = () => {
  const [searchQuery, setSearchQuery] = useAtom(searchQueryAtom);
  const [inputValue, setInputValue] = useState(searchQuery);
  const { schedule: scheduleSearch, cancel: cancelScheduledSearch } = useDebouncedCallback(
    setSearchQuery,
    SEARCH_DEBOUNCE_MS,
  );

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const { value } = event.target;
    setInputValue(value);
    scheduleSearch(value);
  };

  const handleSearch = (value: string) => {
    cancelScheduledSearch();
    setSearchQuery(value);
  };

  return (
    <Input.Search
      size="large"
      allowClear
      placeholder={SEARCH_PLACEHOLDER}
      value={inputValue}
      onChange={handleChange}
      onSearch={handleSearch}
      aria-label="Search files"
    />
  );
};
