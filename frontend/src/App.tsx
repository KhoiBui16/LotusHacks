import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, useLocation } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider } from "@/contexts/AuthContext";
import { LanguageProvider } from "@/contexts/LanguageContext";
import { useEffect } from "react";
import Index from "./pages/Index.tsx";
import CoreServices from "./pages/CoreServices.tsx";
import NotFound from "./pages/NotFound.tsx";
import SignIn from "./pages/SignIn.tsx";
import Dashboard from "./pages/Dashboard.tsx";
import StartClaim from "./pages/StartClaim.tsx";
import IncidentIntake from "./pages/IncidentIntake.tsx";
import Emergency from "./pages/Emergency.tsx";
import ChecklistUpload from "./pages/ChecklistUpload.tsx";
import Validation from "./pages/Validation.tsx";
import ReviewSubmit from "./pages/ReviewSubmit.tsx";
import ClaimTracking from "./pages/ClaimTracking.tsx";
import Vehicles from "./pages/Vehicles.tsx";
import Claims from "./pages/Claims.tsx";
import Notifications from "./pages/Notifications.tsx";
import Settings from "./pages/Settings.tsx";
import ChangePassword from "./pages/ChangePassword.tsx";

const queryClient = new QueryClient();

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <LanguageProvider>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <ScrollToTop />
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/core-services" element={<CoreServices />} />
            <Route path="/sign-in" element={<SignIn />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/start-claim" element={<StartClaim />} />
            <Route path="/incident-intake" element={<IncidentIntake />} />
            <Route path="/emergency" element={<Emergency />} />
            <Route path="/checklist-upload" element={<ChecklistUpload />} />
            <Route path="/validation" element={<Validation />} />
            <Route path="/review-submit" element={<ReviewSubmit />} />
            <Route path="/claim-tracking/:id" element={<ClaimTracking />} />
            <Route path="/vehicles" element={<Vehicles />} />
            <Route path="/claims" element={<Claims />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/change-password" element={<ChangePassword />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
    </LanguageProvider>
  </QueryClientProvider>
);

export default App;
