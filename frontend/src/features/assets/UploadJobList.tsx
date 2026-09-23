import {
  CheckCircleFilled,
  CloseCircleFilled,
  CloseOutlined,
  ExclamationCircleFilled,
  InfoCircleFilled,
} from '@ant-design/icons';
import { Button, Flex, Spin, theme, Typography } from 'antd';
import type { ReactNode } from 'react';

import { TagList } from '@/shared/ui/TagList';

import type { UploadJob, UploadPhase } from './hooks/use-upload-queue';

const ACTIVE_PHASE_TEXT: Partial<Record<UploadPhase, string>> = {
  queued: 'Waiting…',
  uploading: 'Uploading…',
  analyzing: 'Analyzing with AI…',
};

const RESULT_TAG_LIMIT = 8;

interface JobRowProps {
  job: UploadJob;
  icon: ReactNode;
  statusText: ReactNode;
  details?: ReactNode;
  onDismiss?: () => void;
}

const JobRow = ({ job, icon, statusText, details, onDismiss }: JobRowProps) => (
  <Flex
    vertical
    gap={6}
  >
    <Flex
      gap={8}
      align="center"
      wrap
    >
      {icon}
      <Typography.Text
        className="upload-job__filename"
        ellipsis={{ tooltip: job.filename }}
      >
        {job.filename}
      </Typography.Text>
      {statusText}
      {onDismiss && (
        <Button
          type="text"
          size="small"
          icon={<CloseOutlined />}
          aria-label="Dismiss"
          onClick={onDismiss}
        />
      )}
    </Flex>
    {details}
  </Flex>
);

interface UploadJobRowProps {
  job: UploadJob;
  onDismiss: (jobId: string) => void;
}

const UploadJobRow = ({ job, onDismiss }: UploadJobRowProps) => {
  const { token } = theme.useToken();
  const dismiss = () => onDismiss(job.id);

  if (job.phase === 'failed') {
    return (
      <JobRow
        job={job}
        icon={<CloseCircleFilled style={{ color: token.colorError }} />}
        statusText={<Typography.Text type="danger">{job.errorMessage}</Typography.Text>}
        onDismiss={dismiss}
      />
    );
  }

  if (job.phase === 'done' && job.asset) {
    const { asset } = job;
    if (asset.deduplicated) {
      return (
        <JobRow
          job={job}
          icon={<InfoCircleFilled style={{ color: token.colorInfo }} />}
          statusText={<Typography.Text type="secondary">Already in the library.</Typography.Text>}
          onDismiss={dismiss}
        />
      );
    }
    if (asset.status === 'failed') {
      return (
        <JobRow
          job={job}
          icon={<ExclamationCircleFilled style={{ color: token.colorWarning }} />}
          statusText={<Typography.Text type="warning">Saved, but the AI analysis failed.</Typography.Text>}
          details={
            <Typography.Text type="secondary">
              {asset.error ?? 'No details were given.'} Open the file to retry.
            </Typography.Text>
          }
          onDismiss={dismiss}
        />
      );
    }
    return (
      <JobRow
        job={job}
        icon={<CheckCircleFilled style={{ color: token.colorSuccess }} />}
        statusText={<Typography.Text type="success">Ready</Typography.Text>}
        details={
          asset.ai && asset.ai.tags.length > 0 ? (
            <TagList
              tags={asset.ai.tags}
              max={RESULT_TAG_LIMIT}
            />
          ) : undefined
        }
        onDismiss={dismiss}
      />
    );
  }

  return (
    <JobRow
      job={job}
      icon={<Spin size="small" />}
      statusText={<Typography.Text type="secondary">{ACTIVE_PHASE_TEXT[job.phase]}</Typography.Text>}
    />
  );
};

interface UploadJobListProps {
  jobs: UploadJob[];
  onDismiss: (jobId: string) => void;
}

export const UploadJobList = ({ jobs, onDismiss }: UploadJobListProps) => (
  <div
    className="upload-job-list"
    aria-live="polite"
  >
    {jobs.map(job => (
      <UploadJobRow
        key={job.id}
        job={job}
        onDismiss={onDismiss}
      />
    ))}
  </div>
);
