import { Routes, Route, Navigate, Link } from "react-router-dom";
import { ReactNode, lazy, Suspense } from "react";

import useCurrentUser from "../../common/hooks/useCurrentUser";
import Home from "../../pages/home-page/Home";
import Navigation from "../../common/components/TopNavigation";
import LogoWithText from "../../common/components/LogoWithText";
import VisualizerSelect from "../../pages/visualizer-pages/VisualizerSelect";
import LoadingOverlay from "./LoadingOverlay";

import { routeItem } from "./models";
import { HStack } from "@chakra-ui/react";

// * Lazy loading imports for all pages besides index pages
const SignInPage = lazy(() => import("pages/auth-pages/SignIn"));
const TestPage = lazy(() => import("pages/Test"));
const SignUpPage = lazy(() => import("pages/auth-pages/SignUp"));
const ForgotPasswordPage = lazy(
  () => import("pages/auth-pages/ForgotPassword")
);
const ResetPasswordTokenPage = lazy(
  () => import("pages/auth-pages/ResetPasswordToken")
);

const UnlockAccountTokenPage = lazy(
  () => import("pages/auth-pages/UnlockAccountToken")
);
const VerifyEmailPage = lazy(() => import("pages/auth-pages/VerifyEmail"));
const VerifiedEmailTokenPage = lazy(
  () => import("pages/auth-pages/VerifyEmailToken")
);
// * Settings
const SettingsRouterPage = lazy(
  () => import("pages/settings-pages/SettingsRouter")
);
const SettingsEmailPage = lazy(
  () => import("pages/settings-pages/SettingsEmail")
);
const SettingsPasswordPage = lazy(
  () => import("pages/settings-pages/SettingsPassword")
);
const SettingsAccountDetailsPage = lazy(
  () => import("pages/settings-pages/SettingsAccountDetails")
);
const AdminPage = lazy(() => import("pages/dashboard/admin/Admin"));

const VisualizerFormPage = lazy(
  () => import("pages/visualizer-pages/VisualizerForms")
);
const VisualizerEditorPage = lazy(
  () => import("pages/visualizer-pages/VisualizerEditor")
);
const Error404Page = lazy(() => import("pages/Error404"));

/**
 * Object holding all routes responsible for navbar & changing the website name
 */
export const ROUTES: routeItem[] = [
  // * External routing
  { path: ["/"], name: "Home", type: "external" }, // * Index element
  { path: ["/signin"], name: "Sign In", type: "external" },
  { path: ["/signup"], name: "Sign Up", type: "external", hide: false },
  {
    path: ["/forgotpassword"],
    name: "Forgot Passsword",
    hide: true,
    type: "external",
  },
  { path: ["/verify"], name: "Verify Email", type: "external", hide: true },
  // * Internal routing
  { path: ["/", "/visualizers"], name: "Visualizers", type: "internal" }, // * Index element
  {
    path: ["/tool"],
    name: "Tool",
    hide: true,
    type: "internal",
  },
  {
    path: ["/admin"],
    name: "Admin",
    type: "internal",
    admin: true,
  },
  // * Neither internal/external
  {
    path: ["/verify-email/:token"],
    name: "Verify Email",
    type: "none",
    hide: true,
  },
];

type ToggleRouteProps = {
  internal: ReactNode;
  external: ReactNode;
};

/**
 * ToggleRoute
 *
 * Toggle route, render top navigation if external route
 */
const ToggleRoute = ({ internal, external }: ToggleRouteProps) => {
  const { user } = useCurrentUser();
  return <>{user.isLoggedIn ? internal : external}</>;
};

type SwitchRouteProps = {
  component: ReactNode;
};

/**
 * InternalRoute
 *
 * If logged out, navigate to "/signin"
 */
const InternalRoute = ({ component }: SwitchRouteProps) => {
  return (
    <ToggleRoute
      internal={
        <>
          <Navigation />
          {component}
        </>
      }
      external={<Navigate replace to="/signin" />}
    />
  );
};

/**
 * NeutralRoute
 *
 * If logged in, navigate to "/n"
 */
const NeutralRoute = ({ component }: SwitchRouteProps) => {
  return (
    <>
      <HStack w="100%" h={20} justify="center" align="center">
        <Link to="/">
          <LogoWithText />
        </Link>
      </HStack>
      {component}
    </>
  );
};

/**
 * ExternalRoute
 *
 * If logged in, navigate to "/n"
 */
const ExternalRoute = ({ component }: SwitchRouteProps) => {
  return (
    <ToggleRoute
      internal={<Navigate replace to="/" />}
      external={
        <>
          <Navigation />
          {component}
        </>
      }
    />
  );
};

/**
 * ExternalRoute
 *
 * If logged in and not admin, navigate to "/"
 */
const AdminRoute = ({ component }: SwitchRouteProps) => {
  const { user } = useCurrentUser();
  return (
    <>
      <InternalRoute
        component={
          <>
            {user.admin && user?.admin > 0 ? (
              component
            ) : (
              <Navigate replace to="/" />
            )}
          </>
        }
      />
    </>
  );
};

const Router = () => {
  return (
    <Suspense fallback={<LoadingOverlay />}>
      <Routes>
        {/* Index element */}
        <Route
          index
          element={
            <ToggleRoute
              internal={<InternalRoute component={<VisualizerSelect />} />}
              external={<ExternalRoute component={<Home />} />}
            />
          }
        />
        {/* External */}
        <Route
          path="signin"
          element={<ExternalRoute component={<SignInPage />} />}
        />
        <Route
          path="signup"
          element={<ExternalRoute component={<SignUpPage />} />}
        />
        <Route
          path="forgotpassword"
          element={<ExternalRoute component={<ForgotPasswordPage />} />}
        />
        <Route
          path="send-verification-email"
          element={<ExternalRoute component={<VerifyEmailPage />} />}
        />
        {/* Internal */}
        <Route
          path="admin"
          element={<AdminRoute component={<AdminPage />} />}
        />

        {/* Visualizer routes */}
        <Route path="visualizers">
          <Route
            index
            element={<InternalRoute component={<VisualizerSelect />} />}
          />
          <Route
            path="form/:key"
            element={<InternalRoute component={<VisualizerFormPage />} />}
          />
          <Route path="app" element={<VisualizerEditorPage />} />
        </Route>

        <Route path="settings">
          <Route
            index
            element={<InternalRoute component={<SettingsRouterPage />} />}
          />
          <Route
            path="email"
            element={<InternalRoute component={<SettingsEmailPage />} />}
          />
          <Route
            path="password"
            element={<InternalRoute component={<SettingsPasswordPage />} />}
          />
          <Route
            path="account-details"
            element={
              <InternalRoute component={<SettingsAccountDetailsPage />} />
            }
          />
        </Route>

        {/* Testing environment */}
        {process.env.REACT_APP_API_URL === "http://localhost:3000/" ||
          (process.env.REACT_APP_API_URL === "https://dev.scigami.org/" && (
            <Route
              path="test"
              element={<InternalRoute component={<TestPage />} />}
            />
          ))}

        <Route
          path="verify-email/:token"
          element={<NeutralRoute component={<VerifiedEmailTokenPage />} />}
        />
        <Route
          path="unlock-account/:token"
          element={<NeutralRoute component={<UnlockAccountTokenPage />} />}
        />
        <Route
          path="reset-password/:token"
          element={<NeutralRoute component={<ResetPasswordTokenPage />} />}
        />
        <Route
          path="*"
          element={<NeutralRoute component={<Error404Page />} />}
        />
      </Routes>
    </Suspense>
  );
};

export default Router;
