import Link from 'next/link';
import type { UnitDetail } from '@/modules/admin/models';

interface IntroPodcastProps {
  title: string;
  durationSeconds: number | null;
  voice: string | null;
  audioUrl: string | null;
  transcript: string | null;
}

interface LessonPodcastProps {
  id: string;
  title: string;
  order: number;
  hasPodcast: boolean;
  durationSeconds: number | null;
  voice: string | null;
  audioUrl: string | null;
}

interface UnitPodcastListProps {
  introPodcast: IntroPodcastProps | null;
  lessons: LessonPodcastProps[];
}

const resolveAudioHref = (url: string | null): string | null => {
  if (!url) {
    return null;
  }
  if (url.startsWith('http')) {
    return url;
  }
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? '';
  return `${baseUrl}${url}`;
};

const formatDuration = (durationSeconds: number | null): string | null => {
  if (!durationSeconds || durationSeconds <= 0) {
    return null;
  }
  const minutes = Math.floor(durationSeconds / 60);
  const seconds = durationSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')} min`;
};

export const derivePodcastPropsFromUnit = (unit: UnitDetail): UnitPodcastListProps => {
  const intro: IntroPodcastProps | null = unit.has_podcast
    ? {
        title: 'Intro Podcast',
        durationSeconds: unit.podcast_duration_seconds,
        voice: unit.podcast_voice,
        audioUrl: unit.podcast_audio_url,
        transcript: unit.podcast_transcript,
      }
    : null;

  const lessonPodcasts: LessonPodcastProps[] = unit.lessons.map((lesson, idx) => ({
    id: lesson.id,
    title: lesson.title,
    order: idx + 1,
    hasPodcast: lesson.has_podcast,
    durationSeconds: lesson.podcast_duration_seconds,
    voice: lesson.podcast_voice,
    audioUrl: lesson.podcast_audio_url,
  }));

  return {
    introPodcast: intro,
    lessons: lessonPodcasts,
  };
};

export function UnitPodcastList({ introPodcast, lessons }: UnitPodcastListProps) {
  const introHref = resolveAudioHref(introPodcast?.audioUrl ?? null);
  const hasLessonPodcasts = lessons.some((lesson) => lesson.hasPodcast);

  if (!introPodcast && !hasLessonPodcasts) {
    return (
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Intro &amp; Lesson Podcasts</h2>
          <p className="text-sm text-gray-600">Audio assets generated for this unit.</p>
        </div>
        <div className="px-6 py-6 text-sm text-gray-500">
          Podcasts have not been generated for this unit yet.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-medium text-gray-900">Intro &amp; Lesson Podcasts</h2>
        <p className="text-sm text-gray-600">
          Review generated audio for the intro hook and each lesson narrative.
        </p>
      </div>
      <div className="px-6 py-6 space-y-6">
        {introPodcast && (
          <section className="space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <h3 className="text-base font-semibold text-gray-900">Intro Podcast</h3>
              <div className="flex items-center gap-2 flex-wrap">
                {introPodcast.voice && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                    Voice: {introPodcast.voice}
                  </span>
                )}
                {formatDuration(introPodcast.durationSeconds) && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                    {formatDuration(introPodcast.durationSeconds)}
                  </span>
                )}
                {introHref && (
                  <Link
                    href={introHref}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md"
                  >
                    Listen
                  </Link>
                )}
              </div>
            </div>
            {introPodcast.transcript && (
              <div>
                <h4 className="text-xs font-semibold text-gray-700 uppercase mb-2">Transcript</h4>
                <div className="p-4 bg-gray-50 rounded border border-gray-200 text-sm text-gray-700 whitespace-pre-wrap max-h-64 overflow-y-auto">
                  {introPodcast.transcript}
                </div>
              </div>
            )}
            {!introHref && (
              <p className="text-sm text-gray-500">Audio link unavailable.</p>
            )}
          </section>
        )}

        <section>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base font-semibold text-gray-900">Lesson Podcasts</h3>
            {!hasLessonPodcasts && (
              <span className="text-xs text-gray-500">No lesson podcasts generated yet.</span>
            )}
          </div>
          <ul className="space-y-3">
            {lessons.map((lesson) => {
              const lessonHref = resolveAudioHref(lesson.audioUrl);
              return (
                <li
                  key={lesson.id}
                  className="border border-gray-200 rounded-md p-4 bg-gray-50"
                >
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        Lesson {lesson.order}: {lesson.title}
                      </p>
                      <p className="text-xs text-gray-500">Narrated mini-lesson audio</p>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      {lesson.voice && (
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                          Voice: {lesson.voice}
                        </span>
                      )}
                      {formatDuration(lesson.durationSeconds) && (
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                          {formatDuration(lesson.durationSeconds)}
                        </span>
                      )}
                      {lesson.hasPodcast && lessonHref ? (
                        <Link
                          href={lessonHref}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md"
                        >
                          Listen
                        </Link>
                      ) : (
                        <span className="text-xs text-gray-500">Not available</span>
                      )}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </section>
      </div>
    </div>
  );
}
