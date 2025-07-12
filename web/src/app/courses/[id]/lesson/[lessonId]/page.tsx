import Layout from '@/components/Layout'
import LessonViewer from '@/components/LessonViewer'

interface LessonPageProps {
  params: {
    id: string
    lessonId: string
  }
}

export default function LessonPage({ params }: LessonPageProps) {
  return (
    <Layout>
      <LessonViewer courseId={params.id} lessonId={params.lessonId} />
    </Layout>
  )
}