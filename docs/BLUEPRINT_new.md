# BioinfoFlow Web UI Blueprint

## Vision
To launch BioinfoFlow as the most astonishing bioinformatics tool ever—merging a sci-fi-inspired UI with intuitive workflows that captivate and go viral. This isn’t just software; it’s a movement for researchers, students, and innovators.

---

## Key Features
- **Sci-Fi Aesthetic**: Dark mode with neon accents, gradients, and smooth animations that feel futuristic.
- **Interactive Dashboard**: Tiles for workflows, runs, and a “Workflow Spotlight” with community picks.
- **Workflow Canvas**: A live, read-only graph where nodes glow and data flows animate during runs.
- **Run Theater**: Real-time monitoring with progress bars, resource gauges, and searchable logs.
- **Results Playground**: File explorer with previews for FASTA, BAM, etc., plus one-tap visualization in IGV or NGL Viewer.

## Viral Hooks
- **Data Flow Animation**: Mesmerizing visuals of data moving through the pipeline—share-worthy on Reddit.
- **One-Click Sharing**: Public links for runs or workflows with auto-generated thumbnails.
- **Workflow Spotlight**: Curated examples with stunning visuals to inspire users.
- **Guided Tours**: Interactive overlays for learning, perfect for educational buzz on X.com.

---

## Technology Stack
- **Backend**: FastAPI + Pydantic for a robust API.
- **Frontend**: Next.js, React, TypeScript for a slick UI.
- **Styling**: Shadcn UI, Radix UI, Tailwind CSS for beauty and accessibility.
- **Visualization**: React Flow for the canvas; WebAssembly for performance.
- **Real-Time**: Polling (MVP), WebSockets (future).

---

## MVP Scope
1. **Authentication**:
   - Login/signup with OAuth (Google, GitHub).
2. **Workflows**:
   - Upload YAML files or pick from Spotlight.
   - List workflows with metadata.
3. **Runs**:
   - Start runs with a guided config form.
   - Monitor with live status, progress, and logs.
4. **Results**:
   - Browse outputs with previews (text, images, sequences).
   - Visualize in IGV or NGL Viewer with one click.
5. **Workflow Canvas**:
   - Interactive graph with animated data flow and node details on hover.

---

## Design Principles
- **Stunning Simplicity**: Clean layouts with a futuristic edge.
- **Dynamic Feedback**: Animations and live updates that delight.
- **Accessibility**: Keyboard-friendly and screen-reader-ready.
- **Performance**: Optimized for large datasets with WebAssembly.

---

## Development Plan
### Backend (FastAPI)
- **Endpoints**:
  - `/auth/login`, `/auth/signup`
  - `/workflows`, `/workflows/{id}`
  - `/runs`, `/runs/{run_id}`, `/runs/{run_id}/logs`
  - `/results/{run_id}`, `/results/{run_id}/preview/{file}`
- **Integrations**: IGV.js, NGL Viewer for visualizations.

### Frontend (Next.js)
- **Pages**:
  - `/`: Dashboard with Spotlight and tiles.
  - `/workflows`: Workflow list and upload.
  - `/runs/[run_id]`: Run Theater with canvas and logs.
  - `/results/[run_id]`: Results Playground.
- **Components**:
  - `WorkflowCanvas`: Animated graph with React Flow.
  - `RunGauge`: Live progress and resource visuals.
  - `FilePreview`: Dynamic previews by file type.

### Polish
- Add animations (e.g., data flow, node pulses).
- Optimize with caching and lazy loading.
- Test responsiveness on mobile and tablets.

---

## Future Roadmap
- **Drag-and-Drop Canvas**: Build workflows visually.
- **AI Assistant**: Optimize and troubleshoot workflows.
- **Collaboration**: Share and co-edit in real time.
- **Marketplace**: Community hub for workflows.

---

## Why It’ll Go Viral
- **Eye-Candy Visuals**: The animated canvas is a showstopper.
- **Ease + Power**: Perfect for novices and pros alike.
- **Social Ready**: Sharing is built-in and irresistible.
- **Community Seed**: Open-source with Spotlight to spark engagement.

---

## Next Steps
1. Scaffold FastAPI with auth and workflow endpoints.
2. Set up Next.js with the dashboard and canvas.
3. Connect frontend to backend and add polling.
Let’s build this masterpiece together!