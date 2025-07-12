import Layout from '@/components/Layout'
import QuizInterface from '@/components/QuizInterface'

interface QuizPageProps {
  params: {
    id: string
  }
}

export default function QuizPage({ params }: QuizPageProps) {
  return (
    <Layout>
      <QuizInterface quizId={params.id} />
    </Layout>
  )
}