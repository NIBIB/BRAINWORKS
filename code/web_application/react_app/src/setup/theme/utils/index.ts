import {
  blueGenA,
  greenGenA,
  lightBlueGenA,
  orangeGenA,
  pinkGenA,
  purpleGenA,
  redGenA,
  yellowGenA,
} from "../colors";

export function getPallete(index: number) {
  const colors = [
    redGenA,
    orangeGenA,
    yellowGenA,
    greenGenA,
    lightBlueGenA,
    blueGenA,
    pinkGenA,
    purpleGenA,
  ];

  return colors[index % colors.length];
}
