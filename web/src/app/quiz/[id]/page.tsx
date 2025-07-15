import Layout from '@/components/Layout'
import QuizInterface from '@/components/QuizInterface'

interface QuizPageProps {
  params: Promise<{
    id: string
  }>
}

export default async function QuizPage({ params }: QuizPageProps) {
  const { id } = await params
  return (
    <Layout>
      <QuizInterface quizId={id} />
    </Layout>
  )
}