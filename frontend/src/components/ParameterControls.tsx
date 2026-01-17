import type { VideoParams, RampStyle } from '../types';

interface Props {
  params: VideoParams;
  onChange: (params: VideoParams) => void;
}

export function ParameterControls({ params, onChange }: Props) {
  const update = <K extends keyof VideoParams>(key: K, value: VideoParams[K]) => {
    onChange({ ...params, [key]: value });
  };

  return (
    <div className="parameter-controls">
      <h3>Video Settings</h3>

      <fieldset>
        <legend>Speed</legend>

        <label>
          <span>Start WPM: {params.start_wpm}</span>
          <input
            type="range"
            min={50}
            max={500}
            value={params.start_wpm}
            onChange={(e) => update('start_wpm', parseInt(e.target.value))}
          />
        </label>

        <label>
          <span>Peak WPM: {params.peak_wpm}</span>
          <input
            type="range"
            min={100}
            max={1500}
            value={params.peak_wpm}
            onChange={(e) => update('peak_wpm', parseInt(e.target.value))}
          />
        </label>

        <label>
          <span>Ramp Style</span>
          <select
            value={params.ramp_style}
            onChange={(e) => update('ramp_style', e.target.value as RampStyle)}
          >
            <option value="smooth">Smooth (ease-in-out)</option>
            <option value="linear">Linear</option>
            <option value="stepped">Stepped</option>
          </select>
        </label>

        <label>
          <span>Ramp Words (optional)</span>
          <input
            type="number"
            min={10}
            max={500}
            placeholder="Auto (10%)"
            value={params.ramp_words ?? ''}
            onChange={(e) => update('ramp_words', e.target.value ? parseInt(e.target.value) : null)}
          />
        </label>
      </fieldset>

      <fieldset>
        <legend>Chunking (Optional)</legend>
        <label>
          <span>Chunk Duration (seconds)</span>
          <input
            type="number"
            min={5}
            max={300}
            placeholder="No chunking"
            value={params.chunk_duration ?? ''}
            onChange={(e) => update('chunk_duration', e.target.value ? parseFloat(e.target.value) : null)}
          />
          <small>Split long documents into multiple videos</small>
        </label>
      </fieldset>

      <fieldset>
        <legend>Colors</legend>

        <label>
          <span>Background</span>
          <input
            type="color"
            value={params.bg_color}
            onChange={(e) => update('bg_color', e.target.value)}
          />
        </label>

        <label>
          <span>Text</span>
          <input
            type="color"
            value={params.text_color}
            onChange={(e) => update('text_color', e.target.value)}
          />
        </label>

        <label>
          <span>ORP Highlight</span>
          <input
            type="color"
            value={params.orp_color}
            onChange={(e) => update('orp_color', e.target.value)}
          />
        </label>
      </fieldset>

      <fieldset>
        <legend>Dimensions</legend>

        <label>
          <span>Resolution</span>
          <select
            value={`${params.width}x${params.height}`}
            onChange={(e) => {
              const [w, h] = e.target.value.split('x').map(Number);
              onChange({ ...params, width: w, height: h });
            }}
          >
            <option value="1920x1080">1080p (1920x1080)</option>
            <option value="1280x720">720p (1280x720)</option>
            <option value="3840x2160">4K (3840x2160)</option>
            <option value="1080x1920">Vertical 1080p</option>
          </select>
        </label>

        <label>
          <span>Font Size: {params.font_size}px</span>
          <input
            type="range"
            min={24}
            max={200}
            value={params.font_size}
            onChange={(e) => update('font_size', parseInt(e.target.value))}
          />
        </label>
      </fieldset>

      <fieldset>
        <legend>Options</legend>

        <label className="checkbox">
          <input
            type="checkbox"
            checked={params.show_wpm}
            onChange={(e) => update('show_wpm', e.target.checked)}
          />
          <span>Show WPM indicator</span>
        </label>

        <label className="checkbox">
          <input
            type="checkbox"
            checked={params.preprocess}
            onChange={(e) => update('preprocess', e.target.checked)}
          />
          <span>Remove headers/footers (PDF/EPUB)</span>
        </label>
      </fieldset>
    </div>
  );
}
