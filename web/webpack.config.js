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
        {
          test: /\.(json|png|jpe?g|gif|webp|svg|ico)$/, type: 'asset/resource',
          generator: {filename: '[name][ext]'},
        },
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
        maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
        runtimeCaching: [
          {
            urlPattern: /\/download.*(html|js|xml|webp|png|svg|jpe?g|json|css|\/)$/,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'assets',
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
                maxEntries: 20000,
                maxAgeSeconds: 7 * 24 * 3600,
                purgeOnQuotaError: true,
              },
            },
          },
          {
            urlPattern: /\/(tides|forecast|wattsegler)\//,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'tides',
              networkTimeoutSeconds: 10,
              expiration: {
                maxEntries: 1000,
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
    devServer: {
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
      },
      proxy: [
        {
          context: ['/qmap-de', '/qmap-nl', '/download'],
          target: 'https://freenauticalchart.net',
          changeOrigin: true,
        },
        {
          context: ['/tides/de'],
          target: 'https://gezeiten.bsh.de',
          pathRewrite: {'^/tides/de': ''},
          changeOrigin: true,
        },
        {
          context: ['/forecast/de'],
          target: 'https://wasserstand-nordsee.bsh.de',
          pathRewrite: {'^/forecast/de': ''},
          changeOrigin: true,
        },
        {
          context: ['/tides/nl'],
          target: 'https://waterinfo.rws.nl',
          pathRewrite: {'^/tides/nl': ''},
          changeOrigin: true,
        },
        {
          context: ['/wattsegler'],
          target: 'https://www.wattsegler.de',
          pathRewrite: {'^/wattsegler': ''},
          changeOrigin: true,
        },
        {
          context: ['/brightsky'],
          target: 'https://api.brightsky.dev',
          pathRewrite: {'^/brightsky': ''},
          changeOrigin: true,
        },
      ],
    },
  };
};
