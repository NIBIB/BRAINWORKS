/**
 * Function prevents default behavior of form, to reload
 */
export function preventFormSubmission(e: React.KeyboardEvent<HTMLFormElement>) {
  if (e.key === "Enter") {
    e.preventDefault();
  }
}

/**
 * Function that returns true if object has key success
 */
export function containsSuccess(obj: any) {
  return obj?.hasOwnProperty("success");
}

/**
 * Function that returns true if object has key error
 */
export function containsError(obj: any) {
  return obj?.hasOwnProperty("error");
}

/**
 * Function that returns true if string is empty
 */
export function emptyString(s: string) {
  return s.length === 0;
}

/**
 * Function that overwrites the yup to schema object because
 */
export const fixYupToSchemaObject = (s: string) => {};

/**
 * Function that uses binary search to get autocomplete input
 */
const findMatch = (text: string, which = "first", arr: String[]) => {
  if (text) {
    text = text.toLowerCase();
    let start = 0;
    let end = arr.length - 1;
    let candidate_index = null;
    while (start <= end) {
      let mid = Math.floor((start + end) / 2);
      let elem = arr[mid][0].toLowerCase();
      if (elem.substr(0, text.length) === text) {
        candidate_index = mid;
        if (which === "first") end = mid - 1;
        else start = mid + 1;
      } else if (elem < text) start = mid + 1;
      else end = mid - 1;
    }
    return candidate_index;
  }
};
export const matchItems = (text: string, arr: String[]) => {
  let matches: any = [];
  let start = findMatch(text, "first", arr); // get first match
  let end = findMatch(text, "last", arr); // get last match
  if (start != null && end != null) {
    matches = arr.slice(start, end + 1);
  }
  if (matches.length > 0) {
    matches.sort(function (a: string, b: string) {
      return a[1] < b[1] ? 1 : -1;
    });
    matches = matches.slice(0, 5);
  }
  return matches;
};

/**
 * Function that gets all info of field given the property name
 */
export function getFieldInfo(arr: any[], property: string) {
  return arr.filter((item: any) => item.property === property).shift();
}
