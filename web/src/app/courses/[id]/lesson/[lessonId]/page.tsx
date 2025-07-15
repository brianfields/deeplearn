import Layout from '@/components/Layout'
import LessonViewer from '@/components/LessonViewer'

interface LessonPageProps {
  params: Promise<{
    id: string
    lessonId: string
  }>
}

export default async function LessonPage({ params }: LessonPageProps) {
  const { id, lessonId } = await params
  return (
    <Layout>
      <LessonViewer courseId={id} lessonId={lessonId} />
    </Layout>
  )
}