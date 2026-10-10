#!/usr/bin/swift
import Foundation
import Vision
import AppKit

guard CommandLine.arguments.count >= 2 else {
    fputs("usage: ocr_captcha.swift <image-path>\n", stderr)
    exit(2)
}

let path = CommandLine.arguments[1]
let url = URL(fileURLWithPath: path)
guard let image = NSImage(contentsOf: url),
      let tiff = image.tiffRepresentation,
      let bitmap = NSBitmapImageRep(data: tiff),
      let cgImage = bitmap.cgImage
else {
    fputs("failed to load image\n", stderr)
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false
request.recognitionLanguages = ["en-US"]

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
do {
    try handler.perform([request])
} catch {
    fputs("vision error: \(error)\n", stderr)
    exit(1)
}

let observations = request.results ?? []
let text = observations
    .compactMap { $0.topCandidates(1).first?.string }
    .joined()
    .replacingOccurrences(of: " ", with: "")

print(text)
