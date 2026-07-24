import { BrowserRouter } from 'react-router-dom'
import AppRoutes from './routes/AppRoutes'

/** Root component: mounts the router that renders the whole app. */
function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}

export default App
