const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const {GenerateSW} = require('workbox-webpack-plugin');

module.exports = (env, argv) => {
  const isProd = argv.mode === 'production';

  return {
    output: {
      path: path.resolve(__dirname, 'dist'),
      filename: 'bundle.js',
      // filename: isProd ? 'bundle.[contenthash].js' : 'bundle.js',
      clean: true,
    },
    module: {
      rules: [
        // {test: /\.css$/, use: ['style-loader', 'css-loader']},
        {test: /\.css$/, use: [MiniCssExtractPlugin.loader, 'css-loader']},
        {test: /\.less$/, use: [MiniCssExtractPlugin.loader, 'css-loader', 'less-loader']},
        {test: /\.(json|png|jpe?g|gif|webp|svg)$/, type: 'asset/resource', generator: {filename: '[name][ext]'},},
      ],
    },
    plugins: [
      new HtmlWebpackPlugin({
        template: './src/index.html',
        filename: 'index.html',
      }),
      new MiniCssExtractPlugin({
        filename: 'style.css',
        // filename: isProd ? 'style.[contenthash].css' : 'style.css',
      }),
      new GenerateSW({
        mode: isProd ? 'production' : 'development',
        clientsClaim: true,
        skipWaiting: true,
        navigateFallback: '/index.html',
        navigateFallbackAllowlist: [/^\/$/],
        ignoreURLParametersMatching: [/.*/],
        runtimeCaching: [
          {
            urlPattern: /\/download\/.*(html|js|xml|webp|png|jpe?g|json|\/)$/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'other',
              networkTimeoutSeconds: 3,
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 7 * 24 * 3600,
              },
            },
          },
          {
            urlPattern: /\.(webp|pbf)$/,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'tiles',
              expiration: {
                maxEntries: 10000,
                maxAgeSeconds: 7 * 24 * 3600,
              },
            },
          },
        ],
      }),
    ],
    optimization: {
      minimizer: [
        new TerserPlugin({
          terserOptions: {
            compress: {drop_console: isProd},
          },
        }),
        new CssMinimizerPlugin(),
      ],
    },
    watchOptions: {
      ignored: /node_modules|dist/,
      poll: 1000,
    },
  };
};
