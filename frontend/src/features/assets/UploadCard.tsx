import './UploadCard.css';

import { InboxOutlined } from '@ant-design/icons';
import { App, Card, Upload, type UploadProps } from 'antd';

import { ACCEPTED_UPLOAD_TYPES, FILE_TOO_BIG_MESSAGE, UNSUPPORTED_FILE_MESSAGE } from '@/shared/lib/constants';

import { useUploadQueue } from './hooks/use-upload-queue';
import { isAcceptedFile, isFileTooBig } from './upload-limits';
import { UploadJobList } from './UploadJobList';

export const UploadCard = () => {
  const { message } = App.useApp();
  const { jobs, enqueue, dismissJob } = useUploadQueue();

  const beforeUpload: UploadProps['beforeUpload'] = file => {
    if (isFileTooBig(file)) {
      void message.error(FILE_TOO_BIG_MESSAGE);
      return Upload.LIST_IGNORE;
    }
    return true;
  };

  const customRequest: UploadProps['customRequest'] = ({ file }) => {
    if (file instanceof File) {
      enqueue(file);
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
        multiple
        accept={ACCEPTED_UPLOAD_TYPES}
        showUploadList={false}
        beforeUpload={beforeUpload}
        customRequest={customRequest}
        onDrop={onDrop}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">Click or drag files here to upload</p>
        <p className="ant-upload-hint">Text files (.txt, .md) up to 1 MB. Images (JPEG, PNG, WebP, GIF) up to 10 MB.</p>
      </Upload.Dragger>
      {jobs.length > 0 && (
        <UploadJobList
          jobs={jobs}
          onDismiss={dismissJob}
        />
      )}
    </Card>
  );
};
