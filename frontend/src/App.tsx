import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { CampaignEditor } from "./pages/CampaignEditor";
import { CreateCampaign } from "./pages/CreateCampaign";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<CreateCampaign />} />
        <Route path="/editor" element={<CampaignEditor />} />
        <Route path="/campaigns/:id" element={<CampaignEditor />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
