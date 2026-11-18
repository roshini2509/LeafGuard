// Metadata and educational content for the four algorithms.
// Formulas are written in LaTeX and rendered with KaTeX.

export const ALGORITHM_ORDER = ['kmeans', 'hsv', 'histogram', 'canny']

export const DEFAULT_PARAMS = {
  kmeans: { k: 3, max_iterations: 100, tolerance: 0.0001, init_method: 'k-means++', colour_space: 'Lab', seed: 42 },
  hsv: { h_min: 10, h_max: 40, s_min: 25, s_max: 100, v_min: 10, v_max: 70 },
  histogram: {},
  canny: { kernel_size: 5, sigma: 1.4, low: 0.05, high: 0.15, threshold_mode: 'Ratio of max' },
}

export const ALGORITHMS = {
  kmeans: {
    name: 'K-Means Clustering',
    short: 'Groups pixels with similar colour into K clusters.',
    role: 'Groups pixels based on colour similarity.',
    definition:
      'K-Means is an unsupervised clustering algorithm. It splits data points into K groups so that every point belongs to the group whose mean (centroid) is closest to it.',
    purpose:
      'Each pixel is treated as a point in colour space. Healthy tissue, discoloured tissue and background usually have different colours, so they tend to fall into different clusters. You then inspect the clusters and choose which one looks discoloured - the algorithm never decides that by itself.',
    formulas: [
      { label: 'Euclidean distance', tex: 'd(\\mathbf{x},\\mathbf{c}) = \\sqrt{\\sum_{i}(x_i - c_i)^2}' },
      { label: 'Assignment', tex: '\\text{label}(\\mathbf{x}) = \\arg\\min_{j}\\; d(\\mathbf{x},\\mathbf{c}_j)' },
      { label: 'Centroid update', tex: 'C_j = \\frac{1}{N_j}\\sum_{\\mathbf{x}_i \\in C_j}\\mathbf{x}_i' },
      { label: 'Objective (SSE)', tex: 'J = \\sum_{j=1}^{K}\\sum_{\\mathbf{x}\\in C_j}\\lVert\\mathbf{x}-C_j\\rVert^2' },
    ],
    steps: [
      'Read the original image and reshape the H × W × 3 array into N = H·W feature vectors (RGB, or Lab computed by hand).',
      'Initialise K centroids: K random pixels, or K-Means++ (each new centroid chosen with probability proportional to D(x)²).',
      'Compute the Euclidean distance from every pixel to every centroid (an N × K table).',
      'Assign each pixel to its nearest centroid.',
      'Recompute every centroid as the mean of its assigned pixels (an empty cluster is moved to the farthest pixel).',
      'Repeat steps 3-5 until the largest centroid movement is below the tolerance or the iteration limit is reached.',
      'Reconstruct the segmented image by painting every pixel with its cluster’s mean colour.',
    ],
    params: [
      ['K', 'Number of colour clusters (2-8). Raise it if a lesion merges with healthy tissue.'],
      ['Maximum iterations', 'Upper limit on assignment/update rounds.'],
      ['Tolerance', 'Stop when no centroid moves further than this.'],
      ['Initialisation', 'Random pixels, or K-Means++ which spreads the starting centroids apart (more stable).'],
      ['Colour space', 'RGB, or CIE Lab whose a-axis separates green from red/brown.'],
      ['Seed', 'Makes the random choices repeatable.'],
    ],
    stagesInfo: 'Segmented image, false-colour cluster map, one mask per cluster, each cluster on black, SSE per iteration, and the approximate suspected region from the clusters you select.',
    advantages: ['Simple and fast', 'No training data needed', 'Produces regions (masks) directly', 'Easy to explain with colour swatches'],
    limitations: [
      'Uses colour only - no spatial information',
      'K must be chosen by the user',
      'Sensitive to initialisation (fixed with K-Means++ and a seed)',
      'Shadows, soil or old tissue can share a cluster with lesions',
      'A cluster is a colour group, not a disease label',
    ],
    applications: ['Image segmentation', 'Colour quantisation', 'Background removal', 'Crop and soil mapping from aerial images'],
  },
  hsv: {
    name: 'HSV Segmentation',
    short: 'Selects pixels inside chosen Hue, Saturation and Value ranges.',
    role: 'Segments selected colour ranges.',
    definition:
      'HSV segmentation converts every pixel from RGB to Hue (colour angle), Saturation (colour purity) and Value (brightness), then keeps the pixels whose H, S and V all fall inside user-defined ranges.',
    purpose:
      'In HSV the "which colour" information (hue) is separated from brightness, so a colour such as yellow or brown can be selected with simple ranges even when the lighting varies a little. The RGB → HSV conversion is implemented by hand from its equations.',
    formulas: [
      { label: 'Chroma', tex: 'C_{max}=\\max(R,G,B),\\; C_{min}=\\min(R,G,B),\\; \\Delta = C_{max}-C_{min}' },
      {
        label: 'Hue (degrees)',
        tex: 'H = \\begin{cases} 0 & \\Delta = 0 \\\\ 60^\\circ\\left(\\frac{G-B}{\\Delta} \\bmod 6\\right) & C_{max}=R \\\\ 60^\\circ\\left(\\frac{B-R}{\\Delta}+2\\right) & C_{max}=G \\\\ 60^\\circ\\left(\\frac{R-G}{\\Delta}+4\\right) & C_{max}=B \\end{cases}',
      },
      { label: 'Saturation and Value', tex: 'S = \\begin{cases} 0 & C_{max}=0 \\\\ \\Delta / C_{max} & \\text{otherwise}\\end{cases}, \\qquad V = C_{max}' },
      { label: 'Segmentation', tex: 'M(x,y) = [H_{min}\\le H \\le H_{max}] \\wedge [S_{min}\\le S \\le S_{max}] \\wedge [V_{min}\\le V \\le V_{max}]' },
    ],
    steps: [
      'Normalise R, G and B to the range 0-1.',
      'Find the maximum and minimum channel value of each pixel.',
      'Compute the chroma Δ = Cmax − Cmin.',
      'Compute the hue with the case formula (which channel is the maximum).',
      'Compute the saturation S = Δ / Cmax.',
      'Compute the value V = Cmax.',
      'Compare H, S and V of every pixel with the minimum and maximum thresholds. Hue is an angle: if Hmin > Hmax the range wraps around 0° (H ≥ Hmin OR H ≤ Hmax).',
      'Pixels passing all three tests form the foreground mask.',
      'Output the binary segmentation image (white = selected).',
      'Create an overlay that highlights the selected pixels on the original image.',
    ],
    params: [
      ['Hue min / max', '0-360°. Red ≈ 0°, yellow ≈ 60°, green ≈ 120°, blue ≈ 240°.'],
      ['Saturation min / max', '0-100 %. Low saturation = greyish; hue is unreliable there.'],
      ['Value min / max', '0-100 %. Brightness of the pixel.'],
      ['Presets', 'Starting ranges for green, yellow, brown, dark lesions and red/rust - always adjustable.'],
    ],
    stagesInfo: 'Hue (grayscale and as colour), saturation and value channels, the three individual threshold tests, the combined binary mask, the highlighted original and the selected pixels only.',
    advantages: ['Very fast (one pass over the pixels)', 'Thresholds are intuitive', 'Hue is fairly robust to brightness changes', 'Easy to target a specific symptom colour'],
    limitations: [
      'Thresholds must be tuned per image set',
      'Hue is undefined for grey, white and black pixels',
      'Strong lighting changes still shift S and V',
      'Background or stems with the same colour are selected too',
    ],
    applications: ['Skin and fruit colour detection', 'Traffic-sign and object colour tracking', 'Chroma keying (green screen)', 'Crop ripeness grading'],
  },
  histogram: {
    name: 'Histogram Equalization',
    short: 'Spreads intensities over 0-255 to increase contrast.',
    role: 'Enhances intensity contrast.',
    definition:
      'Histogram equalization remaps grey levels through the cumulative distribution of the image so that the output histogram is approximately uniform.',
    purpose:
      'Leaf photos are often low in contrast, so faint discoloration is hard to see. Equalization stretches the most crowded intensity ranges, making subtle intensity differences more visible. It enhances the image; it does not segment anything.',
    formulas: [
      { label: 'Normalised histogram', tex: 'p(r_k) = \\frac{n_k}{M \\cdot N}' },
      { label: 'Cumulative distribution', tex: '\\mathrm{CDF}(r_k) = \\sum_{j=0}^{k} p(r_j)' },
      { label: 'Transformation', tex: 's_k = \\operatorname{round}\\!\\left(255 \\cdot \\frac{\\mathrm{CDF}(r_k)-\\mathrm{CDF}_{min}}{1-\\mathrm{CDF}_{min}}\\right)' },
    ],
    steps: [
      'Read the original image.',
      'Convert to grayscale by hand: Y = 0.299R + 0.587G + 0.114B.',
      'Count n_k, the number of pixels with intensity k, for k = 0…255 (explicit loop).',
      'Divide by the number of pixels M·N to get p(r_k).',
      'Accumulate p(r_k) into the CDF with a running sum.',
      'Find CDF_min, the smallest non-zero CDF value.',
      'Build the 256-entry transformation table s_k with the formula.',
      'Map every pixel r through the table: output = s[r].',
      'Reconstruct the equalized image. A constant image (CDF_min = 1) is returned unchanged to avoid dividing by zero.',
    ],
    params: [['Processing size', 'The only setting: the longest side of the processing copy. Equalization itself has no tunable parameters.']],
    stagesInfo: 'Grayscale image, original histogram, CDF (before and after), equalized histogram, the transformation curve s_k = T(r_k) and before/after comparisons.',
    advantages: ['No parameters to tune', 'Fast: one pass to count, one to map', 'Reveals detail in dark or washed-out images', 'Mathematically simple and exact'],
    limitations: [
      'Amplifies noise in flat regions',
      'Treats background and leaf alike (a bright backdrop takes much of the range)',
      'Can produce unnatural-looking images',
      'Works on intensity only - colour information is not used',
    ],
    applications: ['Medical X-ray and CT enhancement', 'Satellite imagery', 'Low-light photography', 'Pre-processing for other algorithms'],
  },
  canny: {
    name: 'Canny Edge Detection',
    short: 'Multi-stage detector for thin, connected edges.',
    role: 'Detects edges and boundaries.',
    definition:
      'Canny edge detection smooths the image, computes intensity gradients, thins them with non-maximum suppression and keeps edges using two thresholds and connectivity (hysteresis).',
    purpose:
      'It reveals the leaf outline, irregular margins and the boundaries around spots whose brightness differs from the surrounding tissue.',
    formulas: [
      { label: 'Gaussian kernel', tex: 'G_\\sigma(x,y) = \\frac{1}{2\\pi\\sigma^2}\\exp\\!\\left(-\\frac{x^2+y^2}{2\\sigma^2}\\right)' },
      { label: 'Sobel kernels', tex: 'K_x=\\begin{bmatrix}-1&0&1\\\\-2&0&2\\\\-1&0&1\\end{bmatrix},\\quad K_y=\\begin{bmatrix}-1&-2&-1\\\\0&0&0\\\\1&2&1\\end{bmatrix}' },
      { label: 'Magnitude and direction', tex: 'G=\\sqrt{G_x^2+G_y^2}, \\qquad \\theta = \\operatorname{atan2}(G_y, G_x)' },
    ],
    steps: [
      'Convert the original image to grayscale by hand.',
      'Build a Gaussian kernel from the formula and normalise it so its weights sum to 1.',
      'Smooth the image by manual convolution to reduce noise.',
      'Convolve with the Sobel X and Sobel Y kernels to get Gx and Gy.',
      'Compute the gradient magnitude G = √(Gx² + Gy²).',
      'Compute the gradient direction θ = atan2(Gy, Gx) and round it to 0°, 45°, 90° or 135°.',
      'Non-maximum suppression: keep a pixel only if it is ≥ both neighbours along its gradient direction.',
      'Double threshold: strong (≥ upper), weak (between lower and upper), otherwise not an edge.',
      'Hysteresis: starting from strong pixels, keep weak pixels that are 8-connected to them; drop isolated weak pixels.',
    ],
    params: [
      ['Gaussian kernel size', 'Odd window size (3-13).'],
      ['Gaussian sigma', 'Amount of smoothing - more smoothing gives fewer, cleaner edges.'],
      ['Lower threshold', 'Weak-edge threshold.'],
      ['Upper threshold', 'Strong-edge threshold.'],
      ['Threshold mode', 'Ratio of the strongest response (scale-independent) or absolute gradient values.'],
    ],
    stagesInfo: 'Grayscale, Gaussian-smoothed, Gx, Gy, gradient magnitude, gradient direction, non-maximum suppression, strong/weak classification, final edge map and edge overlay.',
    advantages: ['Thin, well-localised edges', 'Robust to noise thanks to smoothing and hysteresis', 'Every stage can be visualised'],
    limitations: [
      'Veins and texture also produce edges',
      'Edges are lines, not filled regions',
      'Sensitive to the thresholds and sigma',
      'Uses intensity only - colour-only boundaries can be missed',
    ],
    applications: ['Object boundary detection', 'Lane detection', 'Document and barcode analysis', 'Pre-processing for shape analysis'],
  },
}
