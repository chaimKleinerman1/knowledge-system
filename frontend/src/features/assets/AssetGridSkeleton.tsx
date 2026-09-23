import { Card, Col, Row, Skeleton } from 'antd';

const SKELETON_COUNT = 8;
const COVER_HEIGHT = 160;

export const AssetGridSkeleton = () => (
  <Row gutter={[16, 16]}>
    {Array.from({ length: SKELETON_COUNT }, (_, index) => (
      <Col
        key={index}
        xs={24}
        sm={12}
        md={8}
        lg={6}
      >
        <Card
          cover={
            <Skeleton.Image
              active
              style={{ width: '100%', height: COVER_HEIGHT }}
            />
          }
          styles={{ body: { padding: 12 } }}
        >
          <Skeleton
            active
            title={{ width: '70%' }}
            paragraph={{ rows: 2 }}
          />
        </Card>
      </Col>
    ))}
  </Row>
);
