import * as Yup from "yup";

export const ACCOUNT_SCHEMA = Yup.object().shape(
  {
    name: Yup.string().required("Required"),
    email: Yup.string().email("Invalid email").required("Required"),
    password: Yup.string()
      .min(8, "Too short!")
      .when(["old_password", "confirm"], {
        is: (a: string, b: string) => a !== undefined || b !== undefined,
        then: Yup.string().required(
          "To change your password, please fill out your current, new and confirmation password"
        ),
      }),
    old_password: Yup.string()
      .min(8, "Too short!")
      .when(["password", "confirm"], {
        is: (a: string, b: string) => a !== undefined || b !== undefined,
        then: Yup.string().required(
          "To change your password, please fill out your current, new and confirmation password"
        ),
      }),
    confirm: Yup.string()
      .min(8, "Too short!")
      .when(["password", "old_password"], {
        is: (a: string, b: string) => a !== undefined || b !== undefined,
        then: Yup.string()
          .required(
            "To change your password, please fill out your current, new and confirmation password"
          )
          .when("password", {
            is: (val: string) => (val && val.length > 0 ? true : false),
            then: Yup.string().oneOf(
              [Yup.ref("password")],
              "Both new and confirm password need to be the same"
            ),
          }),
      }),
    company: Yup.string().max(100).required("Required"),
    country: Yup.string()
      .max(100)
      .notOneOf(["Choose a country"], "Choose a country")
      .required("Required"),
    position: Yup.string()
      .max(50)
      .notOneOf(["Choose a position"], "Choose a position")
      .required("Required"),
    department: Yup.string().max(50),
    purpose: Yup.string().max(200),
  },
  [
    ["old_password", "password"],
    ["password", "confirm"],
    ["old_password", "confirm"],
  ]
);
