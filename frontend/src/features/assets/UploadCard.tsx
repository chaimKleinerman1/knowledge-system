import { InboxOutlined } from '@ant-design/icons';
import { App, Card, Flex, Spin, Typography, Upload, type UploadProps } from 'antd';

import type { AssetResponse } from '@/shared/api/assets';
import { getErrorMessage } from '@/shared/api/http-client';
import { ACCEPTED_UPLOAD_TYPES, FILE_TOO_BIG_MESSAGE, UNSUPPORTED_FILE_MESSAGE } from '@/shared/lib/constants';
import { TagList } from '@/shared/ui/TagList';

import { useUploadAsset } from './hooks/use-upload-asset';
import { isAcceptedFile, isFileTooBig } from './upload-limits';

const RESULT_TAG_LIMIT = 5;

const UploadResult = ({ asset }: { asset: AssetResponse }) => {
  if (asset.deduplicated) {
    return <Typography.Text type="secondary">Already in the library.</Typography.Text>;
  }
  if (asset.status === 'failed') {
    return (
      <Typography.Text type="warning">
        {asset.error ?? 'The AI analysis failed.'} Open the file to retry.
      </Typography.Text>
    );
  }
  return (
    <>
      <Typography.Text type="success">Ready</Typography.Text>
      {asset.ai && (
        <TagList
          tags={asset.ai.tags}
          max={RESULT_TAG_LIMIT}
        />
      )}
    </>
  );
};

export const UploadCard = () => {
  const { message } = App.useApp();
  const upload = useUploadAsset();

  const beforeUpload: UploadProps['beforeUpload'] = file => {
    if (isFileTooBig(file)) {
      void message.error(FILE_TOO_BIG_MESSAGE);
      return Upload.LIST_IGNORE;
    }
    return true;
  };

  const customRequest: UploadProps['customRequest'] = ({ file }) => {
    if (file instanceof File) {
      upload.mutate(file, { onError: error => void message.error(getErrorMessage(error)) });
    }
  };

  const onDrop: UploadProps['onDrop'] = event => {
    // Dropped files outside `accept` never reach beforeUpload or the server, so the message has to come from here.
    const hasUnsupportedFile = Array.from(event.dataTransfer.files).some(file => !isAcceptedFile(file));
    if (hasUnsupportedFile) {
      void message.error(UNSUPPORTED_FILE_MESSAGE);
    }
  };

  return (
    <Card>
      <Upload.Dragger
        multiple={false}
        accept={ACCEPTED_UPLOAD_TYPES}
        disabled={upload.isPending}
        showUploadList={false}
        beforeUpload={beforeUpload}
        customRequest={customRequest}
        onDrop={onDrop}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">Click or drag a file here to upload</p>
        <p className="ant-upload-hint">Text files (.txt, .md) up to 1 MB. Images (JPEG, PNG, WebP, GIF) up to 10 MB.</p>
      </Upload.Dragger>
      {(upload.isPending || upload.isSuccess) && (
        <Flex
          gap={8}
          align="center"
          wrap
          style={{ marginTop: 16 }}
          aria-live="polite"
        >
          {upload.isPending && <Spin size="small" />}
          <Typography.Text ellipsis={{ tooltip: upload.variables.name }}>{upload.variables.name}</Typography.Text>
          {upload.isPending ? (
            <Typography.Text type="secondary">
              {upload.isAnalyzing ? 'Analyzing with AI…' : 'Uploading…'}
            </Typography.Text>
          ) : (
            <UploadResult asset={upload.data} />
          )}
        </Flex>
      )}
    </Card>
  );
};
