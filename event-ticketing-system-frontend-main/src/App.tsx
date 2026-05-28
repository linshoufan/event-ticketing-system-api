import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom"
import { AnimatePresence } from "framer-motion"
import LoginPage from "./pages/LoginPage"
import EventListPage from "./pages/EventListPage"
import EventDetailPage from "./pages/EventDetailPage"
import MyTicketsPage from "./pages/MyTicketsPage"
import TicketDetailPage from "./pages/TicketDetailPage"
import MyTransactionsPage from "./pages/MyTransactionsPage"
import EventManagePage from "./pages/admin/EventManagePage"
import RegistrationDetailPage from "./pages/admin/RegistrationDetailPage"
import UserManagePage from "./pages/admin/UserManagePage"
import CreateEventPage from "./pages/admin/CreateEventPage"
import CheckinPage from "./pages/admin/CheckinPage"
import Navbar from "./components/Navbar"
import HRDashboardPage from "./pages/admin/HRDashboardPage"
import ProfilePage from "./pages/ProfilePage"
import { useAutoLogout } from "./hooks/useAutoLogout"

function Layout() {
  const location = useLocation()
  useAutoLogout()

  const hideNavbar = location.pathname === "/" || location.pathname === "/auth/callback"

  return (
    <>
      {!hideNavbar && <Navbar />}
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<LoginPage />} />
          <Route path="/auth/callback" element={<LoginPage />} />
          <Route path="/events" element={<EventListPage />} />
          <Route path="/events/:eventId" element={<EventDetailPage />} />
          <Route path="/my-transactions" element={<MyTransactionsPage />} />
          <Route path="/my-tickets" element={<MyTicketsPage />} />
          <Route path="/my-tickets/:ticketId" element={<TicketDetailPage />} />
          <Route path="/admin/events" element={<EventManagePage />} />
          <Route path="/admin/events/new" element={<CreateEventPage />} />
          <Route path="/admin/events/:eventId/registrations" element={<RegistrationDetailPage />} />
          <Route path="/admin/events/:eventId/checkin" element={<CheckinPage />} />
          <Route path="/admin/users" element={<UserManagePage />} />
          <Route path="/admin/hr" element={<HRDashboardPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Routes>
      </AnimatePresence>
    </>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  )
}

export default App