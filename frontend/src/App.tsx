import { createBrowserRouter, RouterProvider } from "react-router";
import Home from "./pages/Home";
import ErrorPage from "./pages/ErrorPage";
import AppLayout from "./pages/AppLayout";
import SignIn from "./pages/SignIn";
import UploadMedia from "./pages/UploadMedia";

const router = createBrowserRouter(
  [
    {
      element: <AppLayout />,
      errorElement: <AppLayout children={<ErrorPage />} />,
      children: [
        {
          path: "/",
          element: <Home />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/sign-in",
          element: <SignIn />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/upload-media",
          element: <UploadMedia />,
          errorElement: <ErrorPage />,
        },
        {
          path: "/error",
          element: <ErrorPage />,
          errorElement: <ErrorPage />,
        },
      ],
    },
  ],
  {
    basename: "/true-lens",
  },
);

function App() {
  return <RouterProvider router={router} />;
}

export default App;
