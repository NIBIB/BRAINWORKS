import useCurrentUser from "../../hooks/useCurrentUser";
import NavLink from "./NavLink";
import { ROUTES } from "../../../setup/Router";
import SignupLogoutButtons from "./SignupLogoutButtons";
import InternalNav from "./InternalNav";

const NavRoutes = () => {
  const { user } = useCurrentUser();
  // TODO: create a button option
  return (
    <>
      {ROUTES.map((item) => {
        // * Hide all routes not needed in the navbar
        if (item.hide) {
          return null;
        }
        // * Hide admin routes if user is not admin
        if (!user.admin && item.admin) {
          return null;
        }
        if (user.isLoggedIn)
          if (item.type === "internal") {
            // * If user is logged in, and the it is internal
            return (
              <NavLink underline={true} key={item.name} path={item.path}>
                {item.name}
              </NavLink>
            );
          } else {
            return null;
          }
        // * Otherwise, it is an external path
        else {
          if (item.type === "external") {
            return (
              <NavLink underline={true} key={item.name} path={item.path}>
                {item.name}
              </NavLink>
            );
          } else {
            return null;
          }
        }
      })}
      {user.isLoggedIn && <InternalNav />}
    </>
  );
};

export default NavRoutes;
