import Link from 'next/link';
import type { UnitDetail } from '@/modules/admin/models';

interface IntroPodcastProps {
  title: string;
  durationSeconds: number | null;
  voice: string | null;
  audioUrl: string | null;
  transcript: string | null;
}

interface UnitPodcastListProps {
  introPodcast: IntroPodcastProps | null;
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

  return {
    introPodcast: intro,
  };
};

export function UnitPodcastList({ introPodcast }: UnitPodcastListProps): JSX.Element {
  const introHref = resolveAudioHref(introPodcast?.audioUrl ?? null);

  if (!introPodcast) {
    return (
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Intro Podcast</h2>
          <p className="text-sm text-gray-600">Audio asset generated for the unit intro hook.</p>
        </div>
        <div className="px-6 py-6 text-sm text-gray-500">
          Intro podcast has not been generated for this unit yet.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-medium text-gray-900">Intro Podcast</h2>
        <p className="text-sm text-gray-600">
          Review generated audio for the unit intro hook. Individual lesson podcasts are shown within each lesson's expanded details.
        </p>
      </div>
      <div className="px-6 py-6 space-y-3">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <h3 className="text-base font-semibold text-gray-900">{introPodcast.title}</h3>
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
      </div>
    </div>
  );
}
