import { Alert, Button } from 'antd';

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export const ErrorState = ({ message, onRetry }: ErrorStateProps) => (
  <Alert
    type="error"
    showIcon
    title="Something went wrong"
    description={message}
    action={
      onRetry && (
        <Button
          size="small"
          onClick={onRetry}
        >
          Try again
        </Button>
      )
    }
  />
);
