import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Utility function to merge Tailwind CSS classes
 * Combines clsx and tailwind-merge for intelligent class merging
 * 
 * @example
 * cn("px-2 py-1", "px-3") // => "py-1 px-3"
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
